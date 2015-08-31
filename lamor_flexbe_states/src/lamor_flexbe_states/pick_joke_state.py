#!/usr/bin/env python
import rospy
import random

from flexbe_core import EventState, Logger


class PickJokeState(EventState):
	'''
	Select a joke or pick a random one.

	-- joke_selection 	int 	Index of the joke or 0 for random.

	#> joke 			string 	Provides the selected joke.

	<= done 			Joke has been selected.

	'''

	RANDOM = 0

	def __init__(self, joke_selection):
		super(PickJokeState, self).__init__(outcomes = ['done'],
											output_keys = ['joke'])

		self._joke_selection = joke_selection
		self._jokes = [	'Boy is your name homework because I am not doing you and I should be',
                                 'Are you David Beckham? Because I would bend for you', 'What"s a nice guy like you doing with a body like that',
                   'I am not drunk, I am just intoxicated by you','Your mama is so fat, I took a picture of her last Christmas and its still printing.',
			'Your mama is so stupid, she put two quarters in her ears and thought she was listening to 50 Cent. ', 'I am sorry, I do not think we have met. I would not forget a pretty face like that.','Life without you would be like a broken pencil           pointless.','Can I borrow a kiss? I promise I’ll give it back.' 


                         

		]


	def execute(self, userdata):
		userdata.joke = self._jokes[self._joke_selection - 1]
		return 'done'
		

	def on_enter(self, userdata):
		if self._joke_selection == 0:
			self._joke_selection = random.randint(1, len(self._jokes))
		
