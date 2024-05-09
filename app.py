import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the poker data
poker_data_path = 'poker_data.xlsx'
poker_data = pd.read_excel(poker_data_path, engine='openpyxl')

# Fill None values with 0s and remove rows with all zeros
poker_data.fillna(0, inplace=True)
poker_data = poker_data.loc[~(poker_data==0).all(axis=1)]

# Calculate cumulative earnings
cumulative_earnings = poker_data.cumsum()

# Plotting
fig, ax = plt.subplots()
cumulative_earnings.plot(ax=ax)
ax.set_title('Cumulative Earnings per Player')
ax.set_xlabel('Rounds')
ax.set_ylabel('Earnings')

# Layout
left_column, right_column = st.columns(2)

# Form for updating poker data
with left_column:
    with st.form('update_poker_data'):
        # Input fields for each player's bet
        bets = {}
        for player in poker_data.columns:
            bets[player] = st.number_input(f"Bet for {player}", step=0.1)
        
        # Dropdown to select the winner
        winner = st.selectbox('Select the Winner', options=poker_data.columns)
        
        # Submit button
        submitted = st.form_submit_button('Update Poker Data')
        if submitted:
            # Calculate the new row
            new_row = {player: -bets[player] for player in poker_data.columns}
            new_row[winner] += sum(bets.values())
            
            # Append the new row to the DataFrame
            poker_data = pd.concat([poker_data, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save the updated DataFrame
            poker_data.to_excel(poker_data_path, index=False)
            st.success('Poker data updated successfully!')

# Form for adding a new player
    with st.form('add_player'):
        new_player_name = st.text_input('New Player Name')
        add_player_submitted = st.form_submit_button('Add New Player')
        if add_player_submitted and new_player_name:
            # Add a new column for the player with initial values of 0
            poker_data[new_player_name] = 0
            poker_data.to_excel(poker_data_path, index=False)
            st.success(f'Player {new_player_name} added successfully!')

# Form for removing a player
    with st.form('remove_player'):
        player_to_remove = st.selectbox('Select Player to Remove', options=poker_data.columns)
        confirm_removal_checkbox = st.checkbox('I confirm that I want to remove this player permanently.')
        confirm_removal_text = st.text_input('Type "CONFIRM" to remove the player')
        remove_player_submitted = st.form_submit_button('Remove Player')
        if remove_player_submitted and confirm_removal_checkbox and confirm_removal_text == 'CONFIRM':
            # Remove the player column
            poker_data.drop(columns=[player_to_remove], inplace=True)
            poker_data.to_excel(poker_data_path, index=False)
            st.success(f'Player {player_to_remove} removed successfully!')

# Display the current poker data dynamically
    st.write('Current Poker Data:', poker_data)

# Display the graph
with right_column:
    st.pyplot(fig)