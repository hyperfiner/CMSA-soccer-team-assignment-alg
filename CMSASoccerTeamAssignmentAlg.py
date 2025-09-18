import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Could not import the lzma module.")
import pandas as pd
import numpy as np
import os
import json

def delete_unneeded_columns(data_frame):
# Not needed for 2025 iteration

  # Delete one or more columns by name
  columns_to_keep = ["First Name","Last Name","Have you ever played soccer before?","Please rate your soccer skill level.","Have you played in this league's competitive division in the past three years?","Is there another player with whom you would like to be on the same team? (Requests will be considered but cannot be guaranteed.)","What position do you prefer to play?","What other position would you play, if needed?"] 
  data_frame = data_frame[columns_to_keep]

  return data_frame

def rename_columns(data_frame):

  # Create a dictionary with your transformation rules
  transformation_dict = {
    #"Have you ever played soccer before?": "Experience_YesNo",
    "Please rate your soccer skill level.": "Skill_1to5",
    "Captain Ranking": "Rank",
    "Have you played in this league's competitive division during the recent seasons?": "Competitive_YesNo",
    "Is there another player with whom you would like to be on the same team? (Requests will be considered but cannot be guaranteed.)": "Friend",
    "What position do you prefer to play?": "Position1",
    "What other position would you play, if needed?": "Position2" 
  }

  # Apply the transformation to column headers 
  data_frame = data_frame.rename(columns=transformation_dict)
  
  return data_frame 

def transform_columns(data_frame):

  # Enforce capitalization of first and last names
  data_frame['First Name'] = data_frame['First Name'].apply(lambda x: x.capitalize())
  data_frame['Last Name'] = data_frame['Last Name'].apply(lambda x: x.title())

  # Define transformation rules for each column as a dictionary
  column_rules = {
    "Experience_YesNo": {"Yes, I play regularly.": "Yes", "Yes, I used to play.": "Yes*", "No, I have not played soccer.": "No"},
    "Skill_1to5": {"1 - Novice": 1, "2 - Developing": 2, "3 - Competent": 3, "4 - Proficient": 4, "5 - Expert": 5},
    #"Friend": lambda x: x.upper() if pd.notnull(x) else x,  # Uppercase transformation
    #"Position1": lambda x: x.strip().lower() if pd.notnull(x) else x,  # Strip whitespace, lowercase
    #"Position2": lambda x: x.strip().lower() if pd.notnull(x) else x   # Same as Position1
  }
  
  # Iterate through each column in the DataFrame and apply transformations
  for column,rule in column_rules.items():
    if column in data_frame.columns:
      if isinstance(rule, dict):
        # Apply dictionary-based replacements
        data_frame[column] = data_frame[column].replace(rule)
      else:
        # Apply function-based transformations
        data_frame[column] = data_frame[column].apply(rule)
  
  return data_frame

def add_identifier(data_frame):
  
  data_frame["Unique_ID"] = data_frame.index

  return data_frame

def make_team_assignments(data_frame, n_teams, team_colors, sort_by_rank=True):

  data_frame["Assigned"] = False
  data_frame["Do Not Reassign"] = False
 
  # Create an empty column to store the team assignment
  data_frame["Team"] = np.nan
  last_assigned_team = 0
 
  ## Goalkeeper is a special case
  ###############################

  ## Randomly assign players that have selected Goalkeeper
  ## as their first- or second-choice position

  print("Now randomly assigning Goalkeepers to teams")
  print("-------------------------------------")
  print("-------------------------------------")
  print("-------------------------------------\n")

  for i_position in ["Position1","Position2"]:

    # Grab subset of registrants
    temp_data_frame = data_frame[(data_frame[i_position] == "Goalkeeper")]
    # Randomly re-order subset of registrants
    temp_shuffled_data_frame = temp_data_frame.sample(frac=1, random_state=42).reset_index(drop=True)

    # Distribute registrants into teams in a round-robin fashion
    for idx,row in temp_shuffled_data_frame.iterrows():
      
      # Pull out the unique identifier for this registrant
      unique_ID = temp_shuffled_data_frame.loc[idx,"Unique_ID"]

      # If the player already has a team assignment skip (this should only be true for 
      # anyone that list GK as their primary and secondary position)
      if data_frame.loc[unique_ID,"Assigned"] == True:
        continue

      # Assign the registrant to the next team
      data_frame.loc[unique_ID,"Team"] = team_colors[last_assigned_team%n_teams]
      data_frame.loc[unique_ID,"Assigned"] = True
      data_frame.loc[unique_ID,"Do Not Reassign"] = True # Goalkeepers should not be swappable later on
      print("I'm assigning {0} {1} to {2}".format(data_frame.loc[unique_ID,"First Name"],data_frame.loc[unique_ID,"Last Name"],team_colors[last_assigned_team%n_teams]))
      last_assigned_team += 1

  ## Randomly assign players separately in 
  ## categories of position and competitiveness  
  #############################################

  print("\nNow randomly assigning all other positions to teams")
  print("-------------------------------------")
  print("-------------------------------------")
  print("-------------------------------------")

  if sort_by_rank:
    print_statement = "I'm going to sort based on player's captains-identified ranking.\n"
    sort_categories = [-1,1,2,3,4,5]
    sort_key = "Rank"
  else: # sort by 
    print_statement = "I'm going to sort based on player's history with competitive division.\n"
    sort_categories = ["Yes","No"]
    sort_key = "Competitive_YesNo"

  print(print_statement)

  # Loop over positions
  for position in ["Forward","Midfielder","Defender"]:
    print("\nNow assigning players with preferred position: {0}".format(position))
    print("-------------------------------------")
    print("-------------------------------------")
    # Loop over specified categories
    for sort_it in sort_categories:
      print("\nNow assigning players with {0}: {1}".format(sort_key,sort_it))
      print("-------------------------------------")
      # Grab subset of registrants that have selected position and satisfy sort criterion 
      temp_data_frame = data_frame[(data_frame["Position1"] == position) & (data_frame[sort_key] == sort_it)]
      # Randomly re-order subset of registrants
      temp_shuffled_data_frame = temp_data_frame.sample(frac=1, random_state=42).reset_index(drop=True)

      # Distribute rows into buckets in a round-robin fashion
      for idx,row in temp_shuffled_data_frame.iterrows():
        
        # Pull out the unique identifier for this registrant
        unique_ID = temp_shuffled_data_frame.loc[idx,"Unique_ID"]

        # If the player already has a team assignment skip (this should only be true for secondary goalkeepers)
        if data_frame.loc[unique_ID,"Assigned"] == True:
          continue
        # Assign the registrant to the next team
        data_frame.loc[unique_ID,"Team"] = team_colors[last_assigned_team%n_teams]
        data_frame.loc[unique_ID,"Assigned"] = True
        print("I'm assigning {0} {1} to {2}".format(data_frame.loc[unique_ID,"First Name"],data_frame.loc[unique_ID,"Last Name"],team_colors[last_assigned_team%n_teams]))
        last_assigned_team += 1

  return data_frame

def reassign_player_pairs(data_frame, player_pairs, sort_by_rank=True):

  print("\n\nNow reassigning players to satisfy player pair requests as best as able.")
  print("-------------------------------------")
  print("-------------------------------------")
  print("-------------------------------------\n")

  for pair in player_pairs:
    player_stay = pair[1].split()
    frame_player_stay = data_frame[(data_frame["First Name"] == player_stay[0]) & (data_frame["Last Name"] == " ".join(player_stay[1:]))]
    player_swap = pair[0].split()
    frame_player_swap = data_frame[(data_frame["First Name"] == player_swap[0]) & (data_frame["Last Name"] == " ".join(player_swap[1:]))]

    print("Now attempting to place {0} {1} and {2} {3} on the same team.".format(player_stay[0],player_stay[1],player_swap[0],player_swap[1]))

    # Ensure there's a valid row by checking if the filtered DataFrame is not empty
    if frame_player_stay.empty or frame_player_swap.empty:
      player = player_stay if frame_player_stay.empty else player_swap
      print("WARNING: I don't see this player that you're trying to reassign: {0} ".format(player[0]) + " ".join(player[1:]))
      continue

    # Reset the index of the filtered DataFrames to safely use .loc[0]
    frame_player_stay = frame_player_stay.reset_index(drop=True)
    frame_player_swap = frame_player_swap.reset_index(drop=True)

    team_stay = frame_player_stay.loc[0,"Team"]
    unique_ID_stay = frame_player_stay.loc[0,"Unique_ID"]
    team_swap = frame_player_swap.loc[0,"Team"]
    unique_ID_swap = frame_player_swap.loc[0,"Unique_ID"]

    # Are these players already on the same team?
    if team_stay == team_swap:
      print("{0} {1} and {2} {3} are already on the same team!".format(player_stay[0],player_stay[1],player_swap[0],player_swap[1]))
      print("-------------------------------------\n")

      ## Both players of the pair shouldn't get moved in future swaps
      data_frame.loc[unique_ID_stay,"Do Not Reassign"] = True
      data_frame.loc[unique_ID_swap,"Do Not Reassign"] = True
      
      ## No further action is required
      continue

    position_swap = frame_player_swap.loc[0,"Position1"]
    comp_swap = frame_player_swap.loc[0,"Competitive_YesNo"]
    rank_swap = frame_player_swap.loc[0,"Rank"]

    if sort_by_rank:
      potential_players_to_swap = data_frame[(data_frame["Team"] == team_stay) & (data_frame["Position1"] == position_swap) & (data_frame["Rank"] == rank_swap) & (data_frame["Do Not Reassign"] != True)]
    else:
      potential_players_to_swap = data_frame[(data_frame["Team"] == team_stay) & (data_frame["Position1"] == position_swap) & (data_frame["Competitive_YesNo"] == comp_swap) & (data_frame["Do Not Reassign"] != True)]

    ## If no matches try again, but allow for secondary position of player to be used for matching
    if potential_players_to_swap.empty:
      print("No suitable swaps identified using primary criteria; expanding to allow secondary position to be used for swap")
      if sort_by_rank:
        potential_players_to_swap = data_frame[(data_frame["Team"] == team_stay) & (data_frame["Position2"] == position_swap) & (data_frame["Rank"] == rank_swap) & (data_frame["Do Not Reassign"] != True)]
      else:
        potential_players_to_swap = data_frame[(data_frame["Team"] == team_stay) & (data_frame["Position2"] == position_swap) & (data_frame["Competitive_YesNo"] == comp_swap) & (data_frame["Do Not Reassign"] != True)]

    ## If still no matches, give up on swap
    if potential_players_to_swap.empty:
      print("I can't execute the swap you're attempting because there are no equivalent folks to switch")
      print("-------------------------------------\n")
      continue
  
    random_player_to_swap = potential_players_to_swap.sample(n=1)
    random_player_to_swap = random_player_to_swap.reset_index(drop=True)
    random_player_to_swap_FirstName = random_player_to_swap.loc[0,"First Name"]
    random_player_to_swap_LastName = random_player_to_swap.loc[0,"Last Name"]
    random_player_to_swap_unique_ID = random_player_to_swap.loc[0,"Unique_ID"]
 
    print("I'm going to swap {0} {1} and {2} {3}".format(player_swap[0], player_swap[1], random_player_to_swap_FirstName,random_player_to_swap_LastName))
    print("-------------------------------------\n")

    ## Perform swap
    data_frame.loc[random_player_to_swap_unique_ID,"Team"] = team_swap
    data_frame.loc[unique_ID_swap,"Team"] = team_stay

    ## Both players of the pair shouldn't get moved in future swaps
    data_frame.loc[unique_ID_stay,"Do Not Reassign"] = True
    data_frame.loc[unique_ID_swap,"Do Not Reassign"] = True
 
  return data_frame

def sort_data_by_team(data_frame):

  # Sort data_frame by team
  sorted_data_frame = data_frame.sort_values(by="Team")
  # Reset the index after sorting (optional, to get a clean sequential index)
  sorted_data_frame.reset_index(drop=True, inplace=True)

  return sorted_data_frame
 
def print_stats(data_frame,team_colors,summary_file_path):

  print("\n\nNow printing summary table.")
  print("-------------------------------------")
  print("-------------------------------------")
  print("-------------------------------------\n")

  columns_to_skip = ["First Name","Last Name","Friend","Unique_ID","Assigned","Do Not Reassign","Skill_1to5"]
  summary_table = []

  # Loop through each column except "Team" to get the counts per team
  for column in data_frame.columns:
    if column in columns_to_skip: continue
    if column != "Team":
      #summary_table[column] = data_frame.groupby("Team")[column].value_counts()
      crosstab = pd.crosstab(data_frame["Team"], data_frame[column])
      summary_table.append(crosstab)

  # Concatenate all summary tables into a single DataFrame
  summary_table = pd.concat(summary_table, axis=1)

  print(summary_table)

  # Write the summary table to a text file
  summary_table.to_csv(summary_file_path, sep='\t')

  # Define the manual line to prepend
  manual_line = "\tRank\t\t\t\t\t\tPosition1\t\t\t\tPosition2\t\t\t\tCompetitive_YesNo\t\t\n"
  
  # Prepend the manual line to the summary table content
  temp_content = ""
  with open(summary_file_path, 'r') as summary_file:
    temp_content = summary_file.read() 
  with open(summary_file_path, 'w') as temp_file:
    temp_file.write(manual_line)  # Write the manual line
    temp_file.write(temp_content) # Append the existing summary table

######### I/O #########
#######################
 
file_path = "input/2025_Fall/Fall25_Roster_Open.csv"
output_file_path = "output/2025_Fall/Fall25_Roster_Open_randomized.csv"
summary_file_path = "output/2025_Fall/Fall25_Roster_Open_summary_table.txt"

#### Process Data ####
######################
 
# Read the CSV into a DataFrame
data_frame = pd.read_csv(file_path)
# Delete unneeded columns
#data_frame = delete_unneeded_columns(data_frame)
# Rename column headers
data_frame = rename_columns(data_frame)
# Transform column contents
data_frame = transform_columns(data_frame)
# Add unique identifier
data_frame = add_identifier(data_frame)

### Randomize Data ###
######################

n_teams = 6
team_colors = ["Fandango","Mikado","Gamboge","Amaranth","Glaucous","Vermilion"]
with open("input/2025_Fall/Fall25_Open_player_pairs.json", "r", encoding="utf-8") as f:
    player_pairs = json.load(f)

# Make pseudo-random team assignments
randomized_data_frame = make_team_assignments(data_frame,n_teams,team_colors)
# Attempt to honor player pairing requests
randomized_data_frame = reassign_player_pairs(data_frame,player_pairs)

# Print relevant stats
print_stats(randomized_data_frame,team_colors,summary_file_path)

# Sort by team
sorted_data_frame = sort_data_by_team(randomized_data_frame)

# Remove columns we don't need written out
columns_to_exclude_from_output = ["Friend","Unique_ID","Assigned","Do Not Reassign"]
data_frame_to_write = sorted_data_frame.drop(columns=columns_to_exclude_from_output,errors='ignore')

# Write the rearranged DataFrame back to a new CSV file
data_frame_to_write.to_csv(output_file_path, index=False)

