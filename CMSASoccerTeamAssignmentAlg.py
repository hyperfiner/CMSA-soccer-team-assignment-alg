import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Could not import the lzma module.")
import pandas as pd
import numpy as np
import os
import json

def delete_unneeded_columns(data_frame):

  # Delete one or more columns by name
  columns_to_keep = ["First Name","Last Name","Have you ever played soccer before?","Please rate your soccer skill level.","Have you played in this league's competitive division in the past three years?","Is there another player with whom you would like to be on the same team? (Requests will be considered but cannot be guaranteed.)","What position do you prefer to play?","What other position would you play, if needed?"] 
  data_frame = data_frame[columns_to_keep]

  return data_frame

def rename_columns(data_frame):

  # Create a dictionary with your transformation rules
  transformation_dict = {
    "Have you ever played soccer before?": "Experience_YesNo",
    "Please rate your soccer skill level.": "Skill_1to5",
    "Have you played in this league's competitive division in the past three years?": "Competitive_YesNo",
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

def make_team_assignments(data_frame, n_teams, team_colors):
 
  # Create an empty column to store the team assignment
  data_frame['Team'] = np.nan
  last_assigned_team = 0
 
  ## Goalkeeper is a special case
  ###############################

  # Grab subset of registrants that have selected Goalkeeper as a first- or second-choice position
  temp_data_frame = data_frame[(data_frame["Position1"] == "Goalkeeper") | (data_frame["Position2"] == "Goalkeeper")]
  # Randomly re-order subset of registrants
  temp_shuffled_data_frame = temp_data_frame.sample(frac=1, random_state=42).reset_index(drop=True)

  # Distribute registrants into teams in a round-robin fashion
  for idx,row in temp_shuffled_data_frame.iterrows():
    
    # Pull out the unique identifier for this registrant
    unique_ID = temp_shuffled_data_frame.loc[idx,'Unique_ID']
    # Assign the registrant to the next team
    data_frame.loc[unique_ID,'Team'] = team_colors[last_assigned_team%n_teams]
    last_assigned_team += 1

  ## Randomly assign players separately in 
  ## categories of position and competitiveness  
  #############################################

  # Loop over positions
  for position in ["Forward","Midfielder","Defender"]:
    # Loop over competitiveness
    for comp in ["Yes","No"]:
      
      # Grab subset of registrants that have selected position and are (not) competitive
      temp_data_frame = data_frame[(data_frame["Position1"] == position) & (data_frame["Competitive_YesNo"] == comp)]
      # Randomly re-order subset of registrants
      temp_shuffled_data_frame = temp_data_frame.sample(frac=1, random_state=42).reset_index(drop=True)

      # Distribute rows into buckets in a round-robin fashion
      for idx,row in temp_shuffled_data_frame.iterrows():
        
        # Pull out the unique identifier for this registrant
        unique_ID = temp_shuffled_data_frame.loc[idx,'Unique_ID']
        # Assign the registrant to the next team
        data_frame.loc[unique_ID,'Team'] = team_colors[last_assigned_team%n_teams]
        last_assigned_team += 1

  return data_frame

def reassign_player_pairs(data_frame,player_pairs):

  data_frame["Do Not Reassign"] = False

  ## This is a test
  me = data_frame[(data_frame["First Name"] == "Rob") & (data_frame["Last Name"] == "Fine")]
  me.reset_index(drop=True)
  my_unique_ID = data_frame.loc[0,"Do Not Reassign"] = True

  for pair in player_pairs:
    player_stay = pair[1].split()
    frame_player_stay = data_frame[(data_frame["First Name"] == player_stay[0]) & (data_frame["Last Name"] == " ".join(player_stay[1:]))]
    player_swap = pair[0].split()
    frame_player_swap = data_frame[(data_frame["First Name"] == player_swap[0]) & (data_frame["Last Name"] == " ".join(player_swap[1:]))]

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

      ## Both players of the pair shouldn't get moved in future swaps
      data_frame.loc[unique_ID_stay,"Do Not Reassign"] = True
      data_frame.loc[unique_ID_swap,"Do Not Reassign"] = True
      
      ## No further action is required
      continue

    position_swap = frame_player_swap.loc[0,"Position1"]
    comp_swap = frame_player_swap.loc[0,"Competitive_YesNo"]

    potential_players_to_swap = data_frame[(data_frame["Team"] == team_stay) & (data_frame["Position1"] == position_swap) & (data_frame["Competitive_YesNo"] == comp_swap) & (data_frame["Do Not Reassign"] != True)]

    if potential_players_to_swap.empty:
      print("I can't execute the swap you're attempting because there are no equivalent folks to switch")
      continue
  
    random_player_to_swap = potential_players_to_swap.sample(n=1)
    random_player_to_swap = random_player_to_swap.reset_index(drop=True)
    random_player_to_swap_FirstName = random_player_to_swap.loc[0,"First Name"]
    random_player_to_swap_LastName = random_player_to_swap.loc[0,"Last Name"]
    random_player_to_swap_unique_ID = random_player_to_swap.loc[0,"Unique_ID"]
 
    print("I'm going to swap {0} {1} and {2} {3}".format(player_swap[0], player_swap[1], random_player_to_swap_FirstName,random_player_to_swap_LastName))

    ## Perform swap
    data_frame.loc[random_player_to_swap_unique_ID,"Team"] = team_swap
    data_frame.loc[unique_ID_swap,"Team"] = team_stay

    ## Both players of the pair shouldn't get moved in future swaps
    data_frame.loc[unique_ID_stay,"Do Not Reassign"] = True
    data_frame.loc[unique_ID_swap,"Do Not Reassign"] = True
 
  return data_frame

def sort_data_by_team(data_frame):

  # Sort data_frame by team
  sorted_data_frame = data_frame.sort_values(by='Team')
  # Reset the index after sorting (optional, to get a clean sequential index)
  sorted_data_frame.reset_index(drop=True, inplace=True)

  return sorted_data_frame
 
def print_stats(data_frame,team_colors,summary_file_path):

  columns_to_skip = ["First Name","Last Name","Friend","Unique_ID","Do Not Reassign"]
  summary_table = []

  # Loop through each column except 'Team' to get the counts per team
  for column in data_frame.columns:
    if column in columns_to_skip: continue
    if column != 'Team':
      #summary_table[column] = data_frame.groupby('Team')[column].value_counts()
      crosstab = pd.crosstab(data_frame['Team'], data_frame[column])
      summary_table.append(crosstab)

  # Concatenate all summary tables into a single DataFrame
  summary_table = pd.concat(summary_table, axis=1)

  print(summary_table)

  # Write the summary table to a text file
  summary_table.to_csv(summary_file_path, sep='\t')

  # Define the manual line to prepend
  manual_line = "\tExperience_YesNo\t\t\tSkill_1to5\t\t\t\t\tCompetitive_YesNo\t\tPosition1\t\t\t\tPosition2\t\t\t\t\n"
  
  # Prepend the manual line to the summary table content
  temp_content = ""
  with open(summary_file_path, 'r') as summary_file:
    temp_content = summary_file.read() 
  with open(summary_file_path, 'w') as temp_file:
    temp_file.write(manual_line)  # Write the manual line
    temp_file.write(temp_content) # Append the existing summary table

######### I/O #########
#######################
 
file_path = "input/2024_Fall/Fall24_Roster_Open.csv"
output_file_path = "output/test/Fall24_Roster_Open_randomized.csv"
summary_file_path = "output/test/Fall24_Roster_Open_summary_table.txt"

#### Process Data ####
######################
 
# Read the CSV into a DataFrame
data_frame = pd.read_csv(file_path)
# Delete unneeded columns
data_frame = delete_unneeded_columns(data_frame)
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
with open("input/2024_Fall/Fall24_Open_player_pairs.json", "r", encoding="utf-8") as f:
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
columns_to_exclude_from_output = ["Friend","Unique_ID","Do Not Reassign"]
data_frame_to_write = sorted_data_frame.drop(columns=columns_to_exclude_from_output,errors='ignore')

# Write the rearranged DataFrame back to a new CSV file
data_frame_to_write.to_csv(output_file_path, index=False)

