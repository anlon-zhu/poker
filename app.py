import time
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from streamlit_sortables import sort_items

# Load the poker data
poker_data_path = 'poker_data.xlsx'
poker_data = pd.read_excel(poker_data_path, engine='openpyxl')

# Fill None values with 0s and remove rows with all zeros
poker_data.fillna(0, inplace=True)
poker_data = poker_data.loc[~(poker_data == 0).all(axis=1)]

# Calculate cumulative earnings
cumulative_earnings = poker_data.cumsum()

# Plotting
fig, ax = plt.subplots()
cumulative_earnings.plot(ax=ax)
ax.set_title('Cumulative Earnings per Player')
ax.set_xlabel('Rounds')
ax.set_ylabel('Earnings')

# Poker game state
poker_rounds = ['Pre-flop', 'Flop', 'Turn', 'River', 'End']


def reset_game_state():
    st.session_state['current_round_index'] = 0
    st.session_state['current_player_index'] = 0
    st.session_state['current_bet'] = 0.0
    bets = {}
    for i in range(len(st.session_state['active_players'])):
        bets[i] = 0.0
    st.session_state['bets'] = bets
    st.session_state['folds'] = set()
    st.session_state['looped'] = False
    st.session_state['raise_amt'] = 0.0
    st.session_state['action'] = 'Call'
    st.session_state['web_state'] = 'beginning'


st.session_state['current_round_index'] = st.session_state.get(
    'current_round_index', 0)
st.session_state['current_player_index'] = st.session_state.get(
    'current_player_index', 0)
st.session_state['current_bet'] = st.session_state.get(
    'current_bet', 0.0)
st.session_state['folds'] = st.session_state.get('folds', set())
st.session_state['looped'] = st.session_state.get('looped', False)
st.session_state['raise_amt'] = st.session_state.get(
    'raise_amt', 0.0)
st.session_state['action'] = st.session_state.get('action', 'Call')
# beginning, beginning_sort, play, end
st.session_state['web_state'] = st.session_state.get(
    'web_state', 'beginning')
st.session_state['active_players'] = st.session_state.get(
    'active_players', poker_data.columns.tolist())
bets = {}
for i in range(len(st.session_state['active_players'])):
    bets[i] = 0.0
st.session_state['bets'] = st.session_state.get('bets', bets)


def next_player():
    '''
    Function to update game state and rerender form
    '''
    # Update game state based on last round
    bets = st.session_state['bets']
    folds = st.session_state['folds']
    action = st.session_state['action']
    raise_amt = st.session_state['raise_amt']
    current_player_index = st.session_state['current_player_index']
    players = st.session_state['active_players']

    if action == 'Fold':
        folds.add(current_player_index)
    elif action == 'Raise':
        bets[current_player_index] = raise_amt
        # Convoluted logic because raise_amt is total amount
        st.session_state['bet_delta'] = round(
            raise_amt - st.session_state['current_bet'], 2)
        st.session_state['current_bet'] = bets.get(
            current_player_index, 0.0)
    elif action == 'Call':
        bets[current_player_index] = st.session_state['current_bet']

    # Reset values in case
    st.session_state['action'] = 'Call'
    st.session_state['raise_amt'] = 0.0

    num_players = len(players)

    # Update the current player index
    current_player_index += 1

    while current_player_index % num_players in folds:
        current_player_index += 1

    if current_player_index >= num_players:
        st.session_state['looped'] = True

    current_player_index = current_player_index % num_players
    st.session_state['current_player_index'] = current_player_index

    # round over
    if st.session_state['looped'] and bets[current_player_index] >= st.session_state['current_bet']:
        st.session_state['looped'] = False

        current_player_index = 0
        while current_player_index in folds:
            current_player_index += 1
        st.session_state['current_player_index'] = current_player_index

        if st.session_state[
                'current_round_index'] < len(poker_rounds) - 1:
            st.session_state['current_round_index'] += 1

    if st.session_state['current_round_index'] == len(poker_rounds) - 1 or len(st.session_state['folds']) == num_players - 1:
        st.session_state['web_state'] = 'end'


def number_of_cards(round_index):
    if round_index == 0:
        return 0
    else:
        return round_index + 2


def render_form():
    '''
    Function to render the form
    '''
    current_round = poker_rounds[st.session_state
                                 ['current_round_index']]
    st.subheader(
        f'{current_round} ' + ''.join(
            ['🂡'
             for _ in range(
                 number_of_cards(
                     st.session_state['current_round_index']))]))

    current_bet = st.session_state['current_bet']

    # Highlight the current player and their action
    current_player_index = st.session_state['current_player_index']
    current_player = st.session_state['active_players'][
        current_player_index]

    action_options = ['Call', 'Raise', 'Fold']

    with st.container():
        st.info(f"Waiting for {current_player}... ",
                icon=":material/hourglass:")
        with open('style.css') as f:
            st.markdown(f'<style>{f.read()}</style>',
                        unsafe_allow_html=True)
        action = st.radio(f"Please choose an action:",
                          options=action_options, horizontal=True)

    if action == 'Raise':
        raise_amt = st.number_input(
            f'Enter $ amount {current_player} is raising to',
            min_value=float(current_bet), step=0.1,
            key=f'{current_player}_raise')
        st.session_state['raise_amt'] = round(raise_amt, 2)
    st.session_state['action'] = action
    st.button('End Turn', on_click=next_player)


def render_end():
    bets = st.session_state['bets']
    folds = st.session_state['folds']
    players = st.session_state['active_players']

    st.warning(
        'The game is over! Select the winner and start a new game.')
    # Dropdown to select the winner
    remaining_players = [
        player for i, player in enumerate(players)
        if i not in folds]
    winner = st.selectbox(
        'Select the Winner', options=remaining_players)

    # Submit button
    submitted = st.button('Update Poker Data!')
    if submitted:
        # Calculate the new row
        new_row = {
            player: -bets[i]
            for i, player in enumerate(players)}
        new_row[winner] += sum(bets.values())

        # Append the new row to the DataFrame
        new_data = pd.concat(
            [poker_data, pd.DataFrame([new_row])],
            ignore_index=True)

        # Save the updated DataFrame
        new_data.to_excel(poker_data_path, index=False)
        st.success('Poker data updated successfully!')

        st.session_state['current_round_index'] = 0
        reset_game_state()
        st.rerun()


def render_beginning():
    st.subheader("Who's Gambling?")

    # Default players are active players rotated once
    active_players = st.session_state.get(
        'active_players', poker_data.columns.tolist())
    # rotate the players
    active_players = active_players[1:] + active_players[:1]

    # Checkbox to select players for the game
    selected_players = st.multiselect(
        "", poker_data.columns.tolist(),
        default=active_players)

    # Button to apply the selected players
    apply_players_button = st.button("Submit")

    if apply_players_button:
        # Reorder the DataFrame columns based on the selected players
        st.session_state['active_players'] = selected_players
        st.session_state['web_state'] = 'beginning_sort'
        st.rerun()


def render_beginning_sort():

    # Render the sortable list of selected players
    st.subheader("Set the Order")
    # Centered text for "Dealer" above sorted_players
    st.write(
        "<h6 style='text-align: center;margin-bottom: -6rem;'>Dealer</h6>",
        unsafe_allow_html=True)

    sorted_players = sort_items(
        st.session_state['active_players'],
        direction='vertical')

    # Centered text for "Big Blind" below sorted_players
    st.write(
        "<h6 style='text-align: center; margin-top: -1rem; margin-bottom: -10rem;'>Big Blind</h6>",
        unsafe_allow_html=True)
    big_blind = st.number_input(
        f'Big Blind $ ({sorted_players[-1].title()})',
        min_value=0.0, step=0.1)

    # Button to apply the selected order
    apply_order_button = st.button("Apply Order")

    if apply_order_button:
        st.session_state['active_players'] = sorted_players
        bets = st.session_state['bets']
        # Set the blinds
        bets[len(sorted_players) - 2] = big_blind / 2
        bets[len(sorted_players) - 1] = big_blind

        # Set the current bet at the blind
        st.session_state['current_bet'] = big_blind

        # Success message
        with st.spinner("Starting the game..."):
            time.sleep(1)
        st.session_state['web_state'] = 'play'
        st.rerun()


tab1, tab2 = st.tabs(["Play", "History"])

with tab1:
    # Layout
    left_column, right_column = st.columns(2)
    # Render the form in the left column
    with left_column:
        if st.session_state['web_state'] == 'end':
            render_end()
        elif st.session_state['web_state'] == 'beginning':
            render_beginning()
        elif st.session_state['web_state'] == 'beginning_sort':
            render_beginning_sort()
        elif st.session_state['web_state'] == 'play':
            render_form()

    # Next Player button in the right column
    with right_column:
        if 'beginning' in st.session_state['web_state']:
            with st.container():
                st.image('poker.png', width=250)
        else:
            # Running bet
            st.metric(
                "Current Bet",
                value=f"${st.session_state['current_bet']}",
                delta=f"{st.session_state.get('bet_delta', 0.0)}",
                delta_color="off",
                help="The minimum $ amount to stay in the game")
            # Player bets table
            bets = st.session_state['bets']
            folds = st.session_state['folds']

            player_stakes = {"Player": [], "Stake": []}
            for i, player in enumerate(
                    st.session_state['active_players']):
                stake = bets.get(i, 0.0)
                if i in folds:
                    player = f'{player} (folded)'
                player_stakes["Player"].append(player.title())
                player_stakes["Stake"].append(stake)

            # Convert dictionary to DataFrame
            df = pd.DataFrame(player_stakes, columns=[
                "Player", "Stake"])

            # Function to apply gray color to folded players and blue color to the current player
            def color_highlight(s):
                colors = ['' for _ in range(len(s))]
                for i in range(len(s)):
                    if i in folds:
                        # Gray for folded players
                        colors[i] = 'background-color: rgb(240, 242, 246)'
                    elif i == st.session_state['current_player_index']:
                        # Blue for current player
                        colors[i] = 'background-color: rgba(28, 131, 225, 0.1); color: rgb(0, 66, 128)'
                return colors

            styled_df = df.style.apply(color_highlight)
            # Format stake column to two decimals
            styled_df.format({"Stake": "{:.2f}"})

            st.dataframe(styled_df,
                         column_config={
                             "Stake": st.column_config.NumberColumn(
                                 "$", format="%.2f")},
                         hide_index=True,
                         use_container_width=True)

with tab2:
    # Display the graph
    st.pyplot(fig)

    st.dataframe(poker_data, use_container_width=True)


# Add/remove player functionality
with st.sidebar:
    st.header("Manage Players")
    with st.expander("Add Player", expanded=False):
        new_player_name = st.text_input('New Player Name')
        add_player_submitted = st.button('Add New Player')
        if add_player_submitted and new_player_name:
            # Add a new column for the player with initial values of 0
            poker_data[new_player_name] = 0
            poker_data.to_excel(poker_data_path, index=False)
            st.success(f'Player {new_player_name} added successfully!')

    with st.expander("Remove Player", expanded=False):
        player_to_remove = st.selectbox(
            'Select Player to Remove', options=poker_data.columns)
        confirm_removal_checkbox = st.checkbox(
            'I confirm that I want to remove this player permanently.')
        confirm_removal_text = st.text_input(
            'Type "CONFIRM" to remove the player')
        remove_player_submitted = st.button('Remove Player')
        if remove_player_submitted and confirm_removal_checkbox and confirm_removal_text == 'CONFIRM':
            # Remove the player column
            poker_data.drop(columns=[player_to_remove], inplace=True)
            poker_data.to_excel(poker_data_path, index=False)
            st.success(
                f'Player {player_to_remove} removed successfully!')
