#!/usr/bin/env python

import rospy

from strands_executive_msgs import task_utils
from strands_executive_msgs.msg import Task
from strands_navigation_msgs.msg import TopologicalMap
from strands_navigation_msgs.srv import EstimateTravelTime
from mongodb_store_msgs.msg import StringList
from mongodb_store.message_store import MessageStoreProxy

from datetime import time, date, timedelta
from dateutil.tz import tzlocal

from routine_behaviours.robot_routine import RobotRoutine

import random

class TravelAndRecognizeRoutine(RobotRoutine):
    """ Creates a routine which simply visits nodes. """

    def __init__(self, daily_start, daily_end, idle_duration=rospy.Duration(5), charging_point = 'ChargingPoint'):     
        RobotRoutine.__init__(self, daily_start, daily_end, idle_duration=idle_duration, charging_point=charging_point)
        self.node_names = set()        
        self.topological_map = None
        rospy.Subscriber('topological_map', TopologicalMap, self.map_callback)
        self.random_nodes = []

    def map_callback(self, msg):        
        print 'got map: %s' % len(msg.nodes)
        self.topological_map = msg
        self.node_names = set([node.name for node in msg.nodes if node.name != 'ChargingPoint'])
        if len(self.random_nodes) == 0:
            self.random_nodes = list(self.node_names)

    def get_nodes(self):
        while len(self.node_names) == 0:
            print 'no nodes'
            rospy.sleep(1)
        return self.node_names


    def all_waypoints(self):
        return self.get_nodes()

    def all_waypoints_except(self, exceptions = []):
        return self.all_waypoints() - set(exceptions)


    def max_single_trip_time(self, waypoints):

        expected_time = rospy.ServiceProxy('topological_navigation/travel_time_estimator', EstimateTravelTime)        

        max_time = rospy.Duration(0)
        for start in waypoints:
            for end in waypoints:
                if start != end:
                    et = expected_time(start=start, target=end).travel_time
                    if et > max_time:
                        max_time = et

        return max_time

    def create_travel_routine(self, waypoints=None, daily_start=None, daily_end=None, repeat_delta=None):
        if not waypoints: 
            waypoints = self.get_nodes()

        #if not repeat_delta:
            # ignoring this now            
        #    single_node_estimate = self.max_single_trip_time(waypoints).to_sec()
        #    tour_duration_estimate = single_node_estimate * (len(waypoints)-1) * 2
        #    repeat_delta = timedelta(seconds=tour_duration_estimate)

        #tasks = [ self.create_travel_task(n) for n in waypoints ]
        #self.create_task_routine(tasks=tasks, daily_start=daily_start, daily_end=daily_end, repeat_delta=repeat_delta)

    def create_routine(self):
        
        self.create_travel_routine()

    def on_idle(self):
        """
            Called when the routine is idle. Default is to trigger travel to the charging. As idleness is determined by the current schedule, if this call doesn't utlimately cause a task schedule to be generated this will be called repeatedly.
        """
        if not isinstance(self.random_nodes, list):
            self.random_nodes = list(self.random_nodes)

        rospy.loginfo('Idle for too long, generating a random waypoint task')
        self.add_tasks([self.create_travel_task(random.choice(self.random_nodes))])
    
    def create_travel_task(self, waypoint_name, max_duration=rospy.Duration(30)):
	# Task: robot travels to waypoint and then recognizes object there
	# 
	task = Task()
	task.action = '/flexbe/execute_behavior'
	task_utils.add_string_argument(task,'Example Behavior')
	task.max_duration = max_duration
	task.start_node_id = waypoint_name
	task.end_node_id = waypoint_name
        return task

