from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

NB_SIMULATION = 1000

class CFABot2(BasePokerPlayer):


    def __init__ (self,e_big=0.85, e_little=0.5):
        self.e_big=e_big;
        self.e_little=e_little;

    def declare_action(self, valid_actions, hole_card, round_state):
#        print('bot round_state:',round_state)
        community_card = round_state['community_card']

        if self.nb_player == 1: # only player left, don't run a simulation
              return 'call',0
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=NB_SIMULATION,
                nb_player=self.nb_player,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )

       # Check whether it is possible to call
        can_call = len([item for item in valid_actions if item['action'] == 'call']) > 0
        if can_call:
            # If so, compute the amount that needs to be called
            call_amount = [item for item in valid_actions if item['action'] == 'call'][0]['amount']
        else:
            call_amount = 0
     
        raise_amount_options = [item for item in valid_actions if item['action'] == 'raise'][0]['amount']
        pot = round_state['pot']['main']['amount']

        amount = None
        chance_rate = 1.0/self.nb_player
        EP = 1.e-6
        epsilon = (1-chance_rate/(win_rate+EP))/(1-chance_rate+EP)
#        print('bot pot',pot,'EV',win_rate*pot,'stack',self.my_seat['stack'],'callamt',call_amount,'minraise',raise_amount_options['min'],'maxraise',raise_amount_options['max'],'epsilon %.4f' % epsilon)
        #print('bot: win-rate',win_rate, hole_card, 'epsilon',epsilon, 'nplayers',self.nb_player)

        # If the win rate is large enough, then raise
        if epsilon > 0.0:
            if epsilon > self.e_big:
                # If it is extremely likely to win, then raise as much as possible
                action = 'raise'
                amount = raise_amount_options['max']
            elif epsilon > self.e_little and self.n_small_raises < 1:
                # If it is likely to win, then raise by the minimum amount possible
                action = 'raise'
                amount = raise_amount_options['min']
                self.n_small_raises += 1
            else:
                # If there is a chance to win, then call, but only if it is a small one
                if call_amount <= raise_amount_options['min']*2:
                   action = 'call'
                else:
                   action = 'fold'
        else:
            action = 'call' if can_call and call_amount == 0 else 'fold'

        # Set the amount
        if amount is None:
            items = [item for item in valid_actions if item['action'] == action]
            amount = items[0]['amount']

        return action, amount

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']

    def receive_round_start_message(self, round_count, hole_card, seats):
        # get number of participating players
        np = 0
        for s in seats:
           if s['state']=='participating' or s['state']=='allin':
               np += 1
        self.nb_player = np
#        print('bot: seats',seats)
        pass

    def receive_street_start_message(self, street, round_state):
        #print('bot',self.uuid,'street start')
        self.n_small_raises=0
        for s in round_state['seats']:
            if self.uuid == s['uuid']:
               self.my_seat = s
        pass

    def receive_game_update_message(self, action, round_state):
        # get number of participating players
        #self.nb_player=round_state['table'].seats.count_active_players()
        np = 0
        for s in round_state['seats']:
           if s['state']=='participating' or s['state']=='allin':
               np += 1
        self.nb_player = np
#        print(self.uuid,round_state['street'])
#        print('bot: action histories',round_state['action_histories'][round_state['street']])
#        self.n_small_raises = 0
#        for a in round_state['action_histories'][round_state['street']]:
#            if a['uuid'] == self.uuid:
#               if a['action'] == 'RAISE':
#                  raise_amount_options = [item for item in valid_actions if item['action'] == 'raise'][0]['amount']
        
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

