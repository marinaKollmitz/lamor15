#include <cmath>

#include "stalk/stalk_pose.h"
#include <actionlib/client/simple_action_client.h>

using namespace std;

typedef actionlib::SimpleActionClient<move_base_msgs::MoveBaseAction> Client;

ApproachPerson::ApproachPerson(std::string name) :
    timeToBlink(0),
    timeToUnBlink(0),
    action_name_(name){
    init();
}

void ApproachPerson::init() {

    ros::NodeHandle n;

    listener = new tf::TransformListener();

    // Declare variables that can be modified by launch file or command line.
    //    string pose_array_topic;
    string head_pose_topic;

    // Initialize node parameters from launch file or command line.
    // Use a private node handle so that multiple instances of the node can be run simultaneously
    // while using different parameters.
    ros::NodeHandle private_node_handle_("~");
    //    private_node_handle_.param("pose_array", pose_array_topic, string("/gaze_at_pose/pose_array"));
    private_node_handle_.param("head_pose", head_pose_topic, string("/head/commanded_state"));
    private_node_handle_.param("head_frame", target_frame, string("/head_base_frame"));

    ROS_INFO("Creating stalking action server");
    as_ = new actionlib::SimpleActionServer<stalking::StalkPoseAction>(n, action_name_, false);
    as_->registerGoalCallback(boost::bind(&ApproachPerson::goalCallback, this, n));
    as_->registerPreemptCallback(boost::bind(&ApproachPerson::preemptCallback, this));

    // Create a publisher
    head_pose_pub = n.advertise<sensor_msgs::JointState>(head_pose_topic.c_str(), 10);

    // Connect to MoveBase server
    mbc_ = new actionlib::SimpleActionClient<move_base_msgs::MoveBaseAction>("move_base", true);
    ROS_INFO("Waiting for move_base server...");
    mbc_->waitForServer();

    // Start action server
    as_->start();
    ROS_INFO(" ...stalking server started!");

    transform_thread = boost::thread(&ApproachPerson::transform, this);
}

// Set the endtime for the new goal. 0 = indefinit
void ApproachPerson::goalCallback(ros::NodeHandle &n) {
    goal_ = as_->acceptNewGoal();
    ROS_DEBUG_STREAM("Received goal:\n" << *goal_);
    pose_array_sub = n.subscribe(goal_->topic_name.c_str(), 10, &ApproachPerson::callback, this);
    end_time = goal_->runtime_sec > 0 ? ros::Time::now().toSec() + goal_->runtime_sec : 0.0;

    // Compute goal for robot (keep distance to person)
    geometry_msgs::PoseStamped target = goal_->target;
    geometry_msgs::PoseStamped robot = geometry_msgs::PoseStamped();
    robot.header.frame_id = "base_footprint";
    robot.pose.orientation.w = 1.0;
    try {
        // TODO: Remove hardcoded stuff!
        ROS_DEBUG("Getting robot position.");
        listener->waitForTransform("base_footprint", "map", ros::Time::now(), ros::Duration(3.0));
        listener->transformPose("map", robot, robot);
    }
    catch(tf::TransformException ex) {
        ROS_WARN("Failed transform: %s", ex.what());
    }
    double dx = target.pose.position.x - robot.pose.position.x;
    double dy = target.pose.position.y - robot.pose.position.y;
    double dist = sqrt(dx*dx + dy*dy);
    double angle = atan2(dy,dx);
    double dist_req = 0.7; // Required distance from person
    if (dist > dist_req)
    {
        target.pose.position.x -= dist_req*cos(angle);
        target.pose.position.y -= dist_req*sin(angle);
        target.pose.orientation.w = cos(angle/2);
        target.pose.orientation.z = sin(angle/2);
        // Act only if we are far enough from the person
        move_base_msgs::MoveBaseGoal mb_goal;
        mb_goal.target_pose = target;
        mbc_->sendGoal(mb_goal, boost::bind(&ApproachPerson::MoveBaseDone, this, _1, _2),
                       Client::SimpleActiveCallback(),
                       Client::SimpleFeedbackCallback());
        //mbc_->sendGoal(mb_goal);
    }
}
 
// Done callback for MoveBase

void ApproachPerson::MoveBaseDone(const actionlib::SimpleClientGoalState& state,
                             const move_base_msgs::MoveBaseResultConstPtr &result)
{
    //TODO: should actually parse the result!
    result_.success = true;
    as_->setSucceeded(result_);
    pose_array_sub.shutdown();
}

// Cancel current goal
void ApproachPerson::preemptCallback() {
    ROS_DEBUG("%s: Preempted", action_name_.c_str());

    // set the action state to preempted
    result_.success = false;
    as_->setPreempted(result_);

    // Cancel move_base goal
    mbc_->cancelGoal();

    pose_array_sub.shutdown();

    //resetHead();
}

void ApproachPerson::resetHead() {
    // Publish a zero position to reset the head
    sensor_msgs::JointState state;
    state.header.frame_id = "/head_base_frame";
    state.header.stamp = ros::Time::now();
    state.name.push_back("HeadPan");
    state.name.push_back("HeadTilt");
    state.name.push_back("EyesPan");
    state.name.push_back("EyeLidRight");
    state.name.push_back("EyeLidLeft");
    state.position.push_back(0.0);
    state.position.push_back(0.0);
    state.position.push_back(0.0);
    state.position.push_back(100);
    state.position.push_back(100);

    head_pose_pub.publish(state);
}

//Give feedback about the currently gazed at pose and the remaining run time.
void inline ApproachPerson::feedback(geometry_msgs::Pose pose) {
    feedback_.target = pose;
    feedback_.remaining_time = end_time > 0 ? end_time - ros::Time::now().toSec() : INFINITY;
    as_->publishFeedback(feedback_);
}

//Check if run time is up.
void inline ApproachPerson::checkTime() {
    if(ros::Time::now().toSec() > end_time && end_time > 0.0) {
        ROS_DEBUG("Execution time has been reached. Goal terminated successfully");
        result_.success = true;
        as_->setSucceeded(result_);
        pose_array_sub.shutdown();
        //resetHead();
    }
}

void ApproachPerson::transform() {
    ros::Rate r(10);
    while(ros::ok()) {
        if(as_->isActive()) {
            geometry_msgs::PoseStamped::ConstPtr p = getPose();
            if(p) {
                ROS_DEBUG_STREAM("Using:\n" << *p);
                geometry_msgs::PoseStamped head_coord;
                //Transform into /head_base_frame coordinate system
                try {
                    ROS_DEBUG("Transforming received position into %s coordinate system.", target_frame.c_str());
                    listener->waitForTransform(p->header.frame_id, target_frame, p->header.stamp, ros::Duration(3.0));
                    listener->transformPose(target_frame, ros::Time(0), *p, p->header.frame_id, head_coord);
                }
                catch(tf::TransformException ex) {
                    ROS_WARN("Failed transform: %s", ex.what());
                    continue;
                }

                ROS_DEBUG_STREAM("Transformed into:\n" << head_coord);
                feedback(head_coord.pose);
                checkTime();

                // Create ajoint state to move the head and publish it
                sensor_msgs::JointState state;
                state.header = head_coord.header;
                state.name.push_back("HeadPan");
                state.name.push_back("HeadTilt");
                state.position.push_back(std::atan2(head_coord.pose.position.y, head_coord.pose.position.x) * 180.0 / M_PI);
                state.position.push_back(std::atan2(head_coord.pose.position.z, std::abs(head_coord.pose.position.x)) * 180.0 / M_PI);
                if (ros::Time::now().toSec() >= timeToBlink){
                    state.name.push_back("EyeLids");
                    state.position.push_back(0);
                    timeToUnBlink=ros::Time::now().toSec();
                    timeToBlink=ros::Time::now().toSec()+rand()%28+5;
                }else if (ros::Time::now().toSec() >= timeToUnBlink){
                    state.name.push_back("EyeLids");
                    state.position.push_back(100);
                }

                head_pose_pub.publish(state);
            }
        }
	r.sleep();
    }
}

void ApproachPerson::setPose(const geometry_msgs::PoseStamped::ConstPtr &msg) {
    boost::lock_guard<boost::mutex> lock(mutex);
    pose = msg;
}

const geometry_msgs::PoseStamped::ConstPtr ApproachPerson::getPose() {
    boost::lock_guard<boost::mutex> lock(mutex);
    return pose;
}


void ApproachPerson::callback(const geometry_msgs::PoseStamped::ConstPtr &msg)
{
    if (!as_->isActive())
        return;

    ROS_DEBUG_STREAM("Setting:\n" << *msg);
    setPose(msg);


}



int main(int argc, char **argv)
{
    // Set up ROS.
    std::string action_name = "stalk_pose";
    ros::init(argc, argv, action_name.c_str());

    ApproachPerson *gap = new ApproachPerson(action_name);

    ros::spin();
    return 0;
}
