import re
import time
import sys
import ssl
import os
from collections import OrderedDict
from google_sheets_uploader import append_2d_table_as_values, find_first_empty_row
from googleapiclient.errors import HttpError

# Keywords to filter log entries
KEYWORDS = ["Application Will Terminate", "PostGameCelebration", "Tags: {'", "equipping trainings", "Num Trainings: 2"]
KEYWORDS.extend(["EMatchPhase::VersusScreen", "LogPMSkinDataManager: UPMSkinDataManagerComponent::DetermineLobbyAnimation",
"EMatchPhase::CharacterSelect"])  # Marks the start of a new game



DICT_INTERNAL_TO_EXTERNAL_CHARACTERS = {
    "C_AngelicSupport_C": "Atlas", "C_ChaoticRocketeer_C": "Luna", "C_CleverSummoner_C": "Juno",
    "C_EDMOni_C": "Octavia", "C_EmpoweringEnchanter_C": "Era", "C_FlashySwordsman_C": "Zentaro",
    "C_FlexibleBrawler_C": "Juliette", "C_GravityMage_C": "Finii", "C_HulkingBeast_C": "X",
    "C_MagicalPlaymaker_C": "Ai.Mi", "C_ManipulatingMastermind_C": "Rune", "C_NimbleBlaster_C": "Drek'ar",
    "C_RockOni_C": "Vyce", "C_Shieldz_C": "Asher", "C_SpeedySkirmisher_C": "Kai",
    "C_StalwartProtector_C": "Dubu", "C_TempoSniper_C": "Estelle", "C_UmbrellaUser_C": "Kazan",
    "C_WhipFighter_C": "Rasmus", "C_Healer_C": "Nao", "C_DrumOni_C": "Mako",



    "AngelicSupport": "Atlas", "ChaoticRocketeer": "Luna", "CleverSummoner": "Juno",
    "EDMOni": "Octavia", "EmpoweringEnchanter": "Era", "FlashySwordsman": "Zentaro",
    "FlexibleBrawler": "Juliette", "GravityMage": "Finii", "HulkingBeast": "X",
    "MagicalPlaymaker": "Ai.Mi", "ManipulatingMastermind": "Rune", "NimbleBlaster": "Drek'ar",
    "RockOni": "Vyce", "ShieldUser": "Asher", "SpeedySkirmisher": "Kai",
    "StalwartProtector": "Dubu", "TempoSniper": "Estelle", "UmbrellaUser": "Kazan",
    "WhipFighter": "Rasmus", "Healer": "Nao", "DrumOni": "Mako",
}      #the bottom dict is used for extracting logs from
        #lines with "LogPMSkinDataManager: UPMSkinDataManagerComponent::DetermineLobbyAnimation"
        #for whatever reason Asher's is different between the top and bottom.

DICT_INTERNAL_TO_EXTERNAL_AWAKENINGS = {"TD_AvoidDamageHitHarder": "Glass Cannon", "TD_BarrierBuff": "Demolitionist", "TD_BaseStaggerAndRegen": "Reptile Remedy", "TD_BlessingCooldownRate": "Spark of Focus", "TD_BlessingMaxStagger": "Spark of Resilience", "TD_BlessingPower": "Spark of Strength", "TD_BlessingShare": "Spark of Leadership", "TD_BlessingSpeed": "Spark of Agility", "TD_BuffAndDebuffDuration": "Cast to Last", "TD_ComboATarget": "One-Two Punch", "TD_CreationSize": "Monumentalist", "TD_CreationSizeLifeTime": "Timeless Creator", "TD_DistancePower": "Deadeye", "TD_EdgePower": "Knife's Edge", "TD_EmpoweredHitsBuff": "Specialized Training", "TD_EnergyCatalyst": "Catalyst", "TD_EnergyConversion": "Egoist", "TD_EnergyDischarge": "Fire Up!", "TD_EnhancedOrbsCooldown": "Orb Ponderer" , "TD_EnhancedOrbsSpeed": "Orb Dancer", "TD_FasterDashes": "Super Surge", "TD_FasterDashes2": "Chronoboost", "TD_FasterDashes3": "Explosive Entrance", "TD_FasterProjectiles": "Missile Propulsion", "TD_FasterProjectiles2": "Aerials", "TD_FasterProjectiles3":"Siege Machine", "TD_HitAnythingRestoreStagger": "Tempo Swing", "TD_HitEnemyBurnThem": "Stinger", "TD_HitRockCooldown": "Hotshot", "TD_HitsIncreaseSpeedAndPower": "Stacks On Stacks", "TD_HitSpeed": "Fight Or Flight", "TD_HitsReduceCooldowns": "Perfect Form", "TD_IncreasedPowerWithMaxStagger": "OLD Unstoppable", "TD_IncreasedSpeedWithStagger": "Stagger Swagger", "TD_KOKing": "Prize Fighter", "TD_MovementAbilityCharges": "Twin Drive", "TD_MultiHitsReduceCooldowns": "Heavy Impact", "TD_OrbShare": "Orb Replicator", "TD_PrimaryAbilityCooldownReduction": "Rapid Fire", "TD_PrimaryEcho": "Primetime", "TD_ResistFirstHit": "Unstoppable", "TD_Revive":"Recovery Drone", "TD_ShrinkSelfGrowAllies": "Among Titans", "TD_SizeIncrease": "Built Different", "TD_SizeIncrease2": "Big Fish", "TD_SizePowerConversion": "Might of the Colossus", "TD_SpecialCooldownAfterRounds": "Extra Special", "TD_StackingSize": "Rampage", "TD_StaggerCooldownRateConversion": "Reverberation", "TD_StaggerPowerConversion": "Bulk Up", "TD_StaggerSpeedConversion": "Peak Performance", "TD_StrikeCooldownReduction": "Quick Strike", "TD_StrikeRockTowardsAllies": "Team Player", "TD_TakeDownReduceCooldowns": "Adrenaline Rush"}

DICT_INTERNAL_TO_EXTERNAL_AWAKENINGS.update({"TD_MovementAbilitiesTeleport": "Eject Button", "TD_IncreasedSpeedCrossingMidfield": "Magnetized Soles", "TD_GainRampingSpeed": "Momentum Boots", "TD_HitEnemyDrainThem": "Siphoning Wand", "TD_GoalArcPower": "Powerhouse Pauldrons", "TD_HitStaggerEnemyCooldownReduction": "Pummelers", "TD_StrikeRockSpeedUp": "Slick Kicks", "TD_RangedStrike": "Strike Shot", "TD_KnockAnythingRecoverStagger": "Vicious Vambraces" })




def process_log_entry(line,
CHARACTERS_LIST,
IGN_LIST,
DICT_IGN_TO_AWAKENINGS,
ALL_LOGS_THIS_GAME,
MOST_RECENTLY_PUBLISHED_TABLE
):
    # Clean and filter log entry
    cleaned_line = re.sub(r'^\[.*?\]\[.*?\]', '', line).strip()
    if any(keyword in cleaned_line for keyword in KEYWORDS):



        #print(cleaned_line)

        # Soft reset if new game is detected
        #time.sleep(0.01)
        if "Current[EMatchPhase::CharacterSelect]" in cleaned_line:
            time.sleep(0.01)
            #CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS, ALL_LOGS_THIS_GAME =
            reset_lists(
            CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS, ALL_LOGS_THIS_GAME)

            ALL_LOGS_THIS_GAME.append(cleaned_line)
            return False

        # Avoid duplicate log entries
        if cleaned_line not in ALL_LOGS_THIS_GAME:
            if("LogPMSkinDataManager: UPMSkinDataManagerComponent::DetermineLobbyAnimation" in cleaned_line):
                #then we need to check if EMatchPhase::VersusScreen is a substring in an element of ALL_LOGS_THIS_GAME which is a list of strings.
                if(any("EMatchPhase::VersusScreen" in log_line for log_line in ALL_LOGS_THIS_GAME)== False): #check

                    return False#if EmatchPhase::VersusScreen is not in the logs, then we should not append the current line.

            ALL_LOGS_THIS_GAME.append(cleaned_line)
            #time.sleep(0.1)
            #self.update_signal.emit(cleaned_line)  # Emit signal for new log entry

            # Extract character tags and convert to external names

            if "LogPMSkinDataManager: UPMSkinDataManagerComponent::DetermineLobbyAnimation" in cleaned_line:
                if(len(CHARACTERS_LIST)<6):
                    #print(f"line 109 Characters in the lobby so far {CHARACTERS_LIST}")
                    match = re.search(r"SD_([^_]+)", cleaned_line)
                    if match:
                        extracted_value = match.group(1)
                        converted_value = DICT_INTERNAL_TO_EXTERNAL_CHARACTERS.get(extracted_value)

                    # Optionally, handle the case where the key might not exist
                    if converted_value is None:
                        return
                    else:
                        print("Converted value:", converted_value)
                        if (converted_value not in CHARACTERS_LIST):
                            CHARACTERS_LIST.append(converted_value)
                        if(len(CHARACTERS_LIST)>5):
                            time.sleep(0.01)
                            print(cleaned_line)
                            #for a in ALL_LOGS_THIS_GAME:
                            #    print(a)
                            print(f"line 81, all 6 characters in the lobby: {CHARACTERS_LIST}")

                            #print(ALL_LOGS_THIS_GAME)
                            #we should upload. TODO
                            #self.update_signal.emit("update_characters_display")  # Emit signal to update characters
            # Update player trainings with external names
            elif "equipping trainings" in cleaned_line:
                match = re.search(r"Player '(.+?)' equipping trainings (.*)", cleaned_line)
                if match:
                    player = match.group(1)
                    if player not in IGN_LIST:
                        IGN_LIST.append(player)  # Add player to IGN_LIST
                        #IGN_LIST = sorted(IGN_LIST)
                        #IGN_LIST.sort()
                        #time.sleep(0.1)
                        #print(f"line 98 printing IGN_LIST {IGN_LIST}")
                        if(len(IGN_LIST)==6):
                            IGN_LIST.sort()
                            print(f"line 96 printing IGN_LIST {IGN_LIST}")
                            time.sleep(0.01)
                            #we should upload. TODO

                    trainings = [DICT_INTERNAL_TO_EXTERNAL_CHARACTERS.get(t, t) for t in re.findall(r"TD_\w+", match.group(2)) if t.startswith("TD_")]
                    trainings = [DICT_INTERNAL_TO_EXTERNAL_AWAKENINGS.get(t, t) for t in trainings]
                    existing_trainings = DICT_IGN_TO_AWAKENINGS.get(player, [])  # Use get to avoid KeyError

                    if existing_trainings == trainings:

                        return False
                        #print(f"Trainings for player {player} have not changed.")
                    else:
                        # Update the trainings list and trigger the function
                        time.sleep(0.01)
                        #print(f"Trainings for player {player} have changed.")
                        #print(127)
                        #print(trainings)
                        DICT_IGN_TO_AWAKENINGS[player] = trainings
                        #DICT_IGN_TO_AWAKENINGS = OrderedDict(sorted(DICT_IGN_TO_AWAKENINGS.items()))
                        #print(137)
                        #print(DICT_IGN_TO_AWAKENINGS)
                        #we should consider uploading, return True
                        return True

            elif "Application Will Terminate" in cleaned_line:
                time.sleep(0.01)
                #we should end app here TODO
                print(f"Omega Strikers is terminating log found. Closing this app in 10 seconds.")
                time.sleep(10)
                os._exit(0)


def testfunction(some_number):
    some_number = some_number + 1
    return
def return_true_if_should_upload(google_service, CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS,
ALL_LOGS_THIS_GAME,MOST_RECENTLY_PUBLISHED_TABLE):

    IGN_LIST = sorted(IGN_LIST)

    DICT_IGN_TO_AWAKENINGS = OrderedDict(sorted(DICT_IGN_TO_AWAKENINGS.items()))

    #checks if self.MOST_RECENTLY_PUBLISHED_TABLE is the same as what we would upload.

    #first, construct the table that we WOULD upload.
    candidate_table = CONSTRUCT_UPLOAD_TABLE(CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS)
    #FIRST COLUMN should be characters list

    #SECOND COLUMN should IGN LIST
    #THIRD COLUMN should be that corresponding IGN's


    #if MOST_RECENTLY_PUBLISHED_TABLE is the same as  the candidate,
    #@ we should not upload and return BOOLEAN_CONSIDER_UPLOAD false (?)


    #checks if CHARACTERS_LIST is 6, IGN_LIST is 6. if both are 6 we keep running this function.
    if(len(CHARACTERS_LIST)!= 6 or len(IGN_LIST)!= 6):
        return False

    if iterate_dict_values_true_if_lengths_are_equal(DICT_IGN_TO_AWAKENINGS) is False:
        return False
        #awakening list of each ign is uneven. return False.

    #check if MOST_RECENTLY_PUBLISHED_TABLE is the same as candidate table.
    if(MOST_RECENTLY_PUBLISHED_TABLE==candidate_table):
        return False

    return True



def iterate_dict_values_true_if_lengths_are_equal(DICT_IGN_TO_AWAKENINGS):
    lengths = [len(value) for value in DICT_IGN_TO_AWAKENINGS.values()]

    # Check if all lengths are the same
    return all(length == lengths[0] for length in lengths)
    #returns true if all are the same length.
    #returns false if something is uneven.

def CONSTRUCT_UPLOAD_TABLE(CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS):
    # Initialize the 2D table to store the rows
    upload_table = []
    IGN_LIST = sorted(IGN_LIST)

    DICT_IGN_TO_AWAKENINGS = OrderedDict(sorted(DICT_IGN_TO_AWAKENINGS.items()))
    # Use zip to pair elements from CHARACTERS_LIST and IGN_LIST
    for character, ign in zip(CHARACTERS_LIST, IGN_LIST):
        # Get the list of awakenings for this ign from the dictionary
        awakenings = DICT_IGN_TO_AWAKENINGS.get(ign, [])


        # Create the row and add it to the table
        row = [character, ign] + awakenings  # Append each awakening in a new cell
        while len(row) < 8:
            row.append("")
        upload_table.append(row)

    print(f"upload table:\n{upload_table}")
    return upload_table


def upload_table(google_service,
                 SPREADSHEET_ID,
                 SHEET_NAME,
                 CHARACTERS_LIST,
                 IGN_LIST,
                 DICT_IGN_TO_AWAKENINGS,
                 ALL_LOGS_THIS_GAME,
                 MOST_RECENTLY_PUBLISHED_TABLE):
    """
    Constructs and uploads a table to Google Sheets and updates the most recent table.
    Retries on errors until successful.
    """
    # Construct the table to upload
    upload_this_table = CONSTRUCT_UPLOAD_TABLE(CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS)
    start_row = 1  # Starting row for the upload

    # Define retry logic
    retry_count = 0
    max_retries = 10  # Optional: Limit retries to prevent infinite loops

    while retry_count < max_retries:  # -1 for unlimited retries
        try:
            # Attempt to upload the table
            append_2d_table_as_values(google_service, SPREADSHEET_ID, SHEET_NAME, start_row, upload_this_table)

            # Update MOST_RECENTLY_PUBLISHED_TABLE after successful upload
            MOST_RECENTLY_PUBLISHED_TABLE = upload_this_table
            print("Table uploaded successfully!")
            break  # Exit loop on success

        except (HttpError, ssl.SSLEOFError, Exception) as e:
            # Handle specific errors or general exceptions
            retry_count += 1
            print(f"Error during upload (attempt {retry_count}): {e}")

            # Optional: Raise exception if retry limit is reached
            if retry_count >= max_retries and max_retries != -1:
                print("Max retries reached. Upload failed.")
                raise

            # Wait before retrying (exponential backoff)
            wait_time = max(3, retry_count) #min(2 ** retry_count, 60)  # Max wait time is 60 seconds
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

def reset_lists(CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS, ALL_LOGS_THIS_GAME):

    print('RESETTING LIST. PRINTING DICT_IGN_TO_AWAKENINGS OF LAST GAME...')
    print(IGN_LIST)
    print(DICT_IGN_TO_AWAKENINGS)

    CHARACTERS_LIST.clear()
    IGN_LIST.clear()
    DICT_IGN_TO_AWAKENINGS.clear()
    ALL_LOGS_THIS_GAME.clear()

    #return CHARACTERS_LIST, IGN_LIST, DICT_IGN_TO_AWAKENINGS, ALL_LOGS_THIS_GAME

    #we should check if... the player list and character list is empty. if its empty then return and do nothing.
    #if its not empty, we should...
