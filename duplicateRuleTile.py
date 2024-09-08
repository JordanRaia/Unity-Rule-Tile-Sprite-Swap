import getopt
import sys
import os
import yaml
import re


def main(argv):
    # Define Options: h (for help), p (for path)
    short_opts = "hp:r:s:t:b:f:"
    long_opts = ["help", "palette=", "rule=",
                 "sheet=", "tile", "begin", "filename"]

    palette = ""
    rule = ""
    sheet = ""
    tile = ""
    filename = ""
    begin = 0
    usage_statement = 'Usage: duplicateRuleTile.py -h -p <path_to_palette_folder> -r <path_to_rule_tile_folder> -s <name_of_sprite_sheet> -t <name_of_rule_tile_asset> -b <int_of_new_rule_tile_beginning_sprite> -f [new_filename]'

    try:
        # Parse the arguments using getopt
        opts, args = getopt.getopt(argv, short_opts, long_opts)
    except getopt.GetoptError as err:
        print(err)
        print(usage_statement)
        sys.exit(2)

    # Process each option and argument
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_statement)
            sys.exit()
        elif opt in ("-p", "--palette"):
            palette = arg
        elif opt in ("-r", "--rule"):
            rule = arg
        elif opt in ("-s", "--sheet"):
            sheet = arg
        elif opt in ("-t", "--tile"):
            tile = arg
        elif opt in ("-b", "--begin"):
            begin = int(arg)

    # required args
    if not palette or not sheet or not rule or not begin or not tile:
        print("missing args.")
        sys.exit(2)

    sprites = getSpriteSheetSprites(palette, sheet)
    ruleTile = getRuleTile(rule, tile)

    tileRuleSprites = getRuleTileSpriteOrder(sprites, ruleTile)

    copySpriteRule(rule, sprites, tileRuleSprites, begin, tile, filename)


# classes and functions

def copySpriteRule(rule, sprites, tileRuleSprites, begin, tile, filename):
    # change to rule directory
    os.chdir(rule)

    newRuleTile = []

    change = begin - tileRuleSprites[0].ID

    for sprite in tileRuleSprites:
        id = sprite.ID + change

        for s in sprites:
            if (s.ID == id):
                newRuleTile.append(s)

    with open(tile, 'r') as file:
        content = file.read()

        # Find where the sprite's file id is listed
        search_string = "m_Name: "
        index = content.find(search_string)
        stop_char = " "

        # Get the fileID
        if index != -1:  # if the string is found
            start_index = index + len(search_string)
            after_string = content[start_index:]

            # find position of stop char
            stop_index = after_string.find(stop_char)

            # extract only up to the stop char
            if stop_index != -1:
                name = after_string[:stop_index].strip()
            else:
                name = after_string.strip()

            for i in range(len(newRuleTile)):
                content = content.replace(
                    tileRuleSprites[i].fileID, newRuleTile[i].fileID)

            if filename != "":
                content = content.replace(name, filename)
                f = open(filename + ".asset", "x")
                f.write(content)
                sys.exit()
            else:
                if has_numbers(name):
                    number = re.search(r'\d+', name).group()
                    newNumber = int(re.search(r'\d+', name).group()) + 1
                    newName = name.replace(number, str(newNumber))

                    content = content.replace(name, newName)
                    f = open(newName + ".asset", "x")
                    f.write(content)
                    sys.exit()
                else:
                    newName = name + "_1"
                    content = content.replace(name, newName)

                    f = open(newName + ".asset", "x")
                    f.write(content)
                    sys.exit()


def getRuleTileSpriteOrder(sprites, ruleTile):
    tileRuleSprites = []

    for rule in ruleTile:
        for sprite in sprites:
            if sprite.fileID == str(rule.fileID):
                tileRuleSprites.append(sprite)

    return tileRuleSprites


class UnityLoader(yaml.SafeLoader):
    pass


def ignore_unity_tags(loader, tag_suffix, node):
    return loader.construct_mapping(node, deep=True)


# Register the constructor to handle tags like `!u!114`
UnityLoader.add_multi_constructor('tag:unity3d.com,2011:', ignore_unity_tags)
UnityLoader.add_multi_constructor('!u!', ignore_unity_tags)


def getRuleTile(rule, tile):
    # change to rule directory
    os.chdir(rule)

    tile_rules_list = []

    # open rule tile
    try:
        with open(tile, 'r') as file:
            content = yaml.load(file, Loader=UnityLoader)

            # Ensure content is valid
            if content is None:
                raise ValueError(f"Failed to load YAML from {tile}")

            # Extract m_TilingRules and create TileRule objects
            tiling_rules = content.get(
                'MonoBehaviour', {}).get('m_TilingRules', [])

            for rule in tiling_rules:
                m_Id = rule.get("m_Id")
                fileID = rule.get('m_Sprites', [{}])[0].get('fileID')

                if m_Id is not None and fileID is not None:
                    tile_rule = TileRule(m_Id, fileID)
                    tile_rules_list.append(tile_rule)

    except FileNotFoundError:
        print(f"Error: Tile file '{tile}' not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

    return tile_rules_list


def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)


def getSpriteSheetSprites(palette, sheet):
    # change directory
    os.chdir(palette)

    # get list of files
    files = [f for f in os.listdir('.') if f.startswith(
        sheet) and f.endswith(".asset")]

    # initialize list of Sprites
    sprites = []

    # get list of sprites
    for f in files:
        with open(f, "r") as file:
            # read file
            content = file.read()

            # Find where the sprite's file id is listed
            search_string = "m_Sprite: {fileID: "
            index = content.find(search_string)
            stop_char = ","

            # Get the fileID
            if index != -1:  # if the string is found
                start_index = index + len(search_string)
                after_string = content[start_index:]

                # find position of stop char
                stop_index = after_string.find(stop_char)

                # extract only up to the stop char
                if stop_index != -1:
                    fileID = after_string[:stop_index]
                else:
                    fileID = after_string

                sprite = Sprite(file.name, fileID)
                sprites.append(sprite)

    return sprites


class Sprite:
    def __init__(self, name, fileID):
        self.name = name
        self.fileID = fileID
        self.ID = int(re.search(r'\d+', name).group())

    def display_info(self):
        print(f"Name: {self.name}, File ID: {self.fileID}")


class TileRule:
    def __init__(self, tileID, fileID):
        self.tileID = tileID
        self.fileID = fileID


if __name__ == "__main__":
    main(sys.argv[1:])
