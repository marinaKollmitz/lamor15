#!/usr/bin/env python
###########################################################
#               WARNING: Generated code!                  #
#              **************************                 #
# Manual changes may get lost if file is generated again. #
# Only code inside the [MANUAL] tags will be kept.        #
###########################################################

import roslib; roslib.load_manifest('behavior_tell_random_joke')
from flexbe_core import Behavior, Autonomy, OperatableStateMachine, Logger
from lamor_flexbe_states.detect_person_state import DetectPersonState
from flexbe_states.calculation_state import CalculationState
from flexbe_states.decision_state import DecisionState
from lamor_flexbe_states.speech_output_state import SpeechOutputState
from lamor_flexbe_states.pick_joke_state import PickJokeState
from lamor_flexbe_states.take_picture_state import TakePictureState
from lamor_flexbe_states.store_picture_state import StorePictureState
from flexbe_states.wait_state import WaitState
# Additional imports can be added inside the following tags
# [MANUAL_IMPORT]

# [/MANUAL_IMPORT]


'''
Created on Sun Aug 30 2015
@author: Philipp Schillinger
'''
class TellRandomJokeSM(Behavior):
	'''
	Lets the robot tell a random joke.
	'''


	def __init__(self):
		super(TellRandomJokeSM, self).__init__()
		self.name = 'Tell Random Joke'

		# parameters of this behavior

		# references to used behaviors

		# Additional initialization code can be added inside the following tags
		# [MANUAL_INIT]
		
		# [/MANUAL_INIT]

		# Behavior comments:



	def create(self):
		wait_timeout = 30 # seconds
		max_approach_index = 8
		# x:705 y:482, x:130 y:365
		_state_machine = OperatableStateMachine(outcomes=['finished', 'failed'])
		_state_machine.userdata.approach_index = 0
		_state_machine.userdata.text_too_far = "Sorry, I am unable to come closer! But I can tell you a joke!"
		_state_machine.userdata.text_come_around = "I just took a picture of you. You can come around and take a look."

		# Additional creation code can be added inside the following tags
		# [MANUAL_CREATE]
		
		# [/MANUAL_CREATE]

		# x:282 y:234, x:733 y:240, x:128 y:234
		_sm_approach_person_0 = OperatableStateMachine(outcomes=['finished', 'unable_to_approach', 'no_person'], input_keys=['approach_index'])

		with _sm_approach_person_0:
			# x:92 y:78
			OperatableStateMachine.add('Check_For_Person',
										DetectPersonState(wait_timeout=wait_timeout),
										transitions={'detected': 'Dummy_Approach', 'not_detected': 'no_person'},
										autonomy={'detected': Autonomy.Off, 'not_detected': Autonomy.Off},
										remapping={'person_pose': 'person_pose'})

			# x:448 y:178
			OperatableStateMachine.add('Increment_Index',
										CalculationState(calculation=lambda x: x + 1),
										transitions={'done': 'Check_If_Approach_Choice_Left'},
										autonomy={'done': Autonomy.Off},
										remapping={'input_value': 'approach_index', 'output_value': 'approach_index'})

			# x:609 y:78
			OperatableStateMachine.add('Check_If_Approach_Choice_Left',
										DecisionState(outcomes=['try_next', 'unable'], conditions=lambda idx: 'unable' if idx > max_approach_index else 'try_next'),
										transitions={'try_next': 'Dummy_Approach', 'unable': 'unable_to_approach'},
										autonomy={'try_next': Autonomy.Low, 'unable': Autonomy.High},
										remapping={'input_value': 'approach_index'})

			# x:293 y:78
			OperatableStateMachine.add('Dummy_Approach',
										DecisionState(outcomes=['approached', 'failed'], conditions=lambda x: 'approached' if x > 2 else 'failed'),
										transitions={'approached': 'finished', 'failed': 'Increment_Index'},
										autonomy={'approached': Autonomy.Off, 'failed': Autonomy.Off},
										remapping={'input_value': 'approach_index'})



		with _state_machine:
			# x:82 y:72
			OperatableStateMachine.add('Approach_Person',
										_sm_approach_person_0,
										transitions={'finished': 'Pick_One_Joke', 'unable_to_approach': 'Tell_Too_Far', 'no_person': 'failed'},
										autonomy={'finished': Autonomy.Inherit, 'unable_to_approach': Autonomy.Inherit, 'no_person': Autonomy.Inherit},
										remapping={'approach_index': 'approach_index'})

			# x:444 y:228
			OperatableStateMachine.add('Tell_The_Joke',
										SpeechOutputState(),
										transitions={'done': 'Wait_For_Laughing', 'failed': 'failed'},
										autonomy={'done': Autonomy.Off, 'failed': Autonomy.High},
										remapping={'text': 'joke'})

			# x:244 y:178
			OperatableStateMachine.add('Tell_Too_Far',
										SpeechOutputState(),
										transitions={'done': 'Pick_One_Joke', 'failed': 'failed'},
										autonomy={'done': Autonomy.Low, 'failed': Autonomy.High},
										remapping={'text': 'text_too_far'})

			# x:451 y:78
			OperatableStateMachine.add('Pick_One_Joke',
										PickJokeState(joke_selection=PickJokeState.RANDOM),
										transitions={'done': 'Tell_The_Joke'},
										autonomy={'done': Autonomy.Off},
										remapping={'joke': 'joke'})

			# x:725 y:134
			OperatableStateMachine.add('Take_Picture',
										TakePictureState(),
										transitions={'done': 'Store_Picture'},
										autonomy={'done': Autonomy.Off},
										remapping={'Image': 'Image'})

			# x:709 y:228
			OperatableStateMachine.add('Store_Picture',
										StorePictureState(),
										transitions={'done': 'Say_Come_Around'},
										autonomy={'done': Autonomy.Off},
										remapping={'Image': 'Image'})

			# x:704 y:36
			OperatableStateMachine.add('Wait_For_Laughing',
										WaitState(wait_time=1),
										transitions={'done': 'Take_Picture'},
										autonomy={'done': Autonomy.Off})

			# x:692 y:336
			OperatableStateMachine.add('Say_Come_Around',
										SpeechOutputState(),
										transitions={'done': 'finished', 'failed': 'failed'},
										autonomy={'done': Autonomy.Off, 'failed': Autonomy.Off},
										remapping={'text': 'text_come_around'})


		return _state_machine


	# Private functions can be added inside the following tags
	# [MANUAL_FUNC]
	
	# [/MANUAL_FUNC]
