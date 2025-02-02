import pygame
import screen
import os
import socket
import protocol
import logging
from screen import *

clock = pygame.time.Clock()

BACKGROUND_IMAGE_PATH = os.path.join(PICTURES_PATH, 'opening_screen_picture.png')
bg_image = pygame.image.load(BACKGROUND_IMAGE_PATH)
bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

BACK_BUTTON_IMAGE_PATH = os.path.join(PICTURES_PATH, 'back_sign.png')
back_button_image = pygame.image.load(BACK_BUTTON_IMAGE_PATH)
back_button_image = pygame.transform.scale(back_button_image, (int(SCREEN_WIDTH/10), int(SCREEN_HEIGHT/10)))

REFRESH_BUTTON_IMAGE_PATH = os.path.join(PICTURES_PATH, 'refresh_button.png')
refresh_button_image = pygame.image.load(REFRESH_BUTTON_IMAGE_PATH)
refresh_button_image = pygame.transform.scale(refresh_button_image,
                                              (back_button_image.get_width(), back_button_image.get_height()))

SOUNDS_PATH = 'sounds'


PASSIVE_TEXTBOX_COLOR = colors.WHITE
ACTIVE_TEXTBOX_COLOR = colors.LIGHT_BLUE

PIECES_SET_RECT_WIDTH = 200
PIECES_SET_RECT_HEIGHT = 100
PIECES_SET_RECT_PADDING = 20



BOT_GAME_TYPE = 1
ONLINE_GAME_TYPE = 2
TWO_PLAYERS_GAME_TYPE = 3


# Keys in rectangles dict
START_GAME = 0
NUMBER_OF_PLAYERS = 1
GAME_LENGTH = 2
BOT_LEVEL = 3
TEAM_SELECTION = 4
ONLINE_GAME = 5
BACK_BUTTON = 8
JOIN_GAME_RECTS = 9
REFRESH_BUTTON = 10
PIECES_SET = 11
BOARD_SET = 12 


MAX_USERNAME_LENGTH = 10

ONE_RECT_GROUPS = [START_GAME, ONLINE_GAME, BACK_BUTTON, REFRESH_BUTTON]

# default values
is_board_set_one = True
is_pieces_set_one = False
is_one_players_playing = True
game_length = 5  # In minutes.
level = 3  # Bot Depth
is_white = True
username = ""
my_socket = None
opponent_player_name = ""
game_type = BOT_GAME_TYPE

TEXT_BOX_HEIGHT = REGULAR_FONT.get_height() + 20
TEXT_BOX_WIDTH = 600


class WaitingGame:
    def __init__(self, name, is_other_player_white, current_game_length):
        self.opponent_player_name = name
        self.is_white = not is_other_player_white
        self.length = current_game_length


def starting_screen():
    global game_type
    game_type = BOT_GAME_TYPE if is_one_players_playing else TWO_PLAYERS_GAME_TYPE

    # Print background image.
    screen.blit(bg_image, (0, 0))

    # Print title.
    text = LARGE_FONT.render("Sahmaster", False, colors.YELLOW)
    screen.blit(text, (SCREEN_WIDTH / 2 - text.get_width() / 2, 50))

    rectangles = set_rectangles()
    while True:
        pygame.display.flip()

        for event in pygame.event.get():
            handle_event(event, rectangles)


def online_screen(*ignore):
    global username
    global game_type
    global my_socket

    game_type = ONLINE_GAME_TYPE
    screen.blit(bg_image, (0, 0))
    back_button_rect = draw_and_get_back_button()

    # Print title.
    text = LARGE_FONT.render("ENTER YOUR NAME:", False, colors.DARK_BLUE)
    screen.blit(text, (SCREEN_WIDTH / 2 - text.get_width() / 2, 100))

    # Text box rectangle to get input from user.
    text_box = pygame.Rect(MIDDLE_HORIZONTAL - TEXT_BOX_WIDTH/2, SCREEN_HEIGHT/2, TEXT_BOX_WIDTH, TEXT_BOX_HEIGHT)

    create_game_rect, join_game_rect, create_game_text, join_game_text = get_join_create_rectangles(text_box)

    # Colors of text box
    is_active = False
    draw_text_box(username, text_box, is_active)
    while True:
        pygame.display.flip()
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                raise exceptions.UserExitGame

            if event.type == pygame.MOUSEBUTTONDOWN:
                if text_box.collidepoint(pygame.mouse.get_pos()):
                    is_active = True
                else:
                    is_active = False
                draw_text_box(username, text_box, is_active)

                if back_button_rect.collidepoint(pygame.mouse.get_pos()):
                    return starting_screen()

                if create_game_rect.collidepoint(pygame.mouse.get_pos()):
                    if len(username) > 0:
                        create_game()
                    else:
                        pygame.mixer.Sound(os.path.join(SOUNDS_PATH, 'error.wav')).play()

                if join_game_rect.collidepoint(pygame.mouse.get_pos()):
                    if len(username) > 0:
                        join_game_screen()
                    else:
                        pygame.mixer.Sound(os.path.join(SOUNDS_PATH, 'error.wav')).play()

            if is_active and event.type == pygame.KEYDOWN:

                # Delete last letter.
                if event.key == pygame.K_BACKSPACE:
                    username = username[:-1]

                elif len(username) < MAX_USERNAME_LENGTH:
                    username += event.unicode

                draw_text_box(username, text_box, is_active)

            # deactivate create and join game rect.
            if len(username) == 0:
                pygame.draw.rect(screen, colors.WHITE, create_game_rect)
                pygame.draw.rect(screen, colors.WHITE, join_game_rect)

            # Activate create and join game rect.
            else:
                pygame.draw.rect(screen, colors.LIGHT_BLUE, create_game_rect)
                pygame.draw.rect(screen, colors.LIGHT_BLUE, join_game_rect)

            # The 25 is padding from rect and text
            screen.blit(create_game_text, (MIDDLE_HORIZONTAL - create_game_text.get_width() / 2, create_game_rect.top + 25))
            screen.blit(join_game_text, (MIDDLE_HORIZONTAL - join_game_text.get_width() / 2, join_game_rect.top + 25))


def get_join_create_rectangles(textbox: pygame.Rect) -> tuple:
    text = REGULAR_FONT.render("JOIN GAME", False, colors.BLACK)
    join_game_rect = pygame.Rect(MIDDLE_HORIZONTAL - (text.get_width() / 2 + 50),
                                 textbox.bottom + text.get_height() + 50, text.get_width() + 100, text.get_height() + 50)

    pygame.draw.rect(screen, colors.YELLOW, join_game_rect)
    screen.blit(text, (join_game_rect.centerx - text.get_width() / 2, join_game_rect.centery - text.get_height() / 2))
    join_game_text = text

    text = REGULAR_FONT.render("CREATE GAME", False, colors.BLACK)
    create_game_rect = pygame.Rect(MIDDLE_HORIZONTAL - (text.get_width() / 2 + 50),
                                   join_game_rect.bottom + text.get_height() + 50,
                                   text.get_width() + 100, text.get_height() + 50)
    pygame.draw.rect(screen, colors.WHITE, create_game_rect)
    screen.blit(text, (create_game_rect.centerx - text.get_width() / 2, create_game_rect.top + 25))
    create_game_text = text
    return create_game_rect, join_game_rect, create_game_text, join_game_text


def join_game_screen(*ignore):
    global opponent_player_name
    rectangles = dict()

    # Print background.
    screen.blit(bg_image, (0, 0))

    rectangles[BACK_BUTTON] = draw_and_get_back_button()
    rectangles[REFRESH_BUTTON] = draw_and_get_refresh_button()
    # Join server.
    connect_to_server()
    final_request = protocol.Request(username, protocol.GET_GAMES).set_request_to_server()

    my_socket.send(final_request)
    games_list = get_games_list()
    logging.debug(f"Games list is: {games_list}")
    rectangles[JOIN_GAME_RECTS] = create_join_game_rectangles(games_list)

    while True:
        pygame.display.flip()
        for event in pygame.event.get():
            try:
                handle_event(event, rectangles)

            except exceptions.BackToLastScreen:
                online_screen()

            except exceptions.JoinGameError:
                pygame.mixer.Sound(os.path.join(SOUNDS_PATH, 'error.wav')).play()


def create_game():
    global opponent_player_name

    screen.blit(bg_image, (0, 0))
    connect_to_server()

    logging.debug("Creating game")
    msg_content = "1" if is_white else "0"
    msg_content += str(game_length).zfill(2)
    my_socket.send(protocol.Request(username, protocol.CREATE_GAME, msg_content).set_request_to_server())
    text = LARGE_FONT.render("waiting for second player...", False, colors.DARK_BLUE)
    screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/2 - text.get_height()/2))
    pygame.display.flip()

    opponent_player_name_length = int(my_socket.recv(1).decode())
    opponent_player_name = my_socket.recv(opponent_player_name_length).decode()
    raise exceptions.FinishStartingScreen


def create_join_game_rectangles(games_name: list):
    rectangle_width = int(SCREEN_WIDTH * (3/4))
    rectangle_height = REGULAR_FONT.get_height() + 20
    last_rectangle_bottom = 0
    rectangles = dict()
    for game in games_name:
        text_string = f"opponent player is: {game.opponent_player_name} - "
        your_team = "white team" if game.is_white else "black team"
        text_string += f"your team: {your_team} - "
        text_string += f"game length: {str(game.length)}"
        text = REGULAR_FONT.render(text_string, False, colors.WHITE)
        current_game_rect = pygame.Rect(MIDDLE_HORIZONTAL - int(rectangle_width/2),
                                        last_rectangle_bottom + rectangle_height, rectangle_width, rectangle_height)
        last_rectangle_bottom = current_game_rect.bottom
        rectangles[game] = current_game_rect
        pygame.draw.rect(screen, colors.DARK_BLUE, current_game_rect)
        screen.blit(text, (MIDDLE_HORIZONTAL - text.get_width()/2, current_game_rect.top + 10))

        # Rect wouldn't be out of screen
        if last_rectangle_bottom + (rectangle_height*2) >= SCREEN_HEIGHT:
            break

    pygame.display.flip()
    return rectangles


def get_games_list() -> list:
    """"
    :return A list with all data of the games waiting for second player
    data of game including: first player name, is first player white, game length
    """
    games = list()
    list_length = my_socket.recv(1).decode()
    logging.debug(f"number of players waiting for their games is {list_length}")
    for x in range(int(list_length)):
        name_length = int(my_socket.recv(1).decode())
        name = my_socket.recv(name_length).decode()
        is_opponent_player_white = int(my_socket.recv(1).decode())
        current_game_length = int(my_socket.recv(2).decode())
        games.append(WaitingGame(name, is_opponent_player_white, current_game_length))
    return games


def draw_text_box(username, text_box, is_active):
    text_box_color = ACTIVE_TEXTBOX_COLOR if is_active else PASSIVE_TEXTBOX_COLOR
    pygame.draw.rect(screen, text_box_color, text_box)
    text = REGULAR_FONT.render(username, False, colors.BLACK)
    screen.blit(text, (text_box.left + 10, text_box.top + 10))


def connect_to_server():
    global my_socket
    if my_socket is not None:
        return
    my_socket = socket.socket()
    my_socket.connect((protocol.SERVER_IP, protocol.SERVER_PORT))


def set_rectangles():
    rectangles = dict()
    # Print start game rect.
    text = REGULAR_FONT.render("START GAME", False, colors.BLACK)
    rect_high = text.get_height() + 50
    rect_width = text.get_width() + 50
    start_game_rect = pygame.Rect(MIDDLE_HORIZONTAL - rect_width/2, 550, rect_width, rect_high)
    pygame.draw.rect(screen, colors.YELLOW, start_game_rect)
    screen.blit(text, (start_game_rect.centerx - text.get_width() / 2, start_game_rect.centery - text.get_height() / 2))
    rectangles[START_GAME] = start_game_rect

    # Print online game rect
    text = REGULAR_FONT.render("ONLINE GAME", False, colors.BLACK)
    rect_width = text.get_width() + 50
    rect_high = text.get_height() + 50
    online_game_rect = pygame.Rect(MIDDLE_HORIZONTAL - rect_width / 2, start_game_rect.top+200, rect_width, rect_high)
    pygame.draw.rect(screen, colors.YELLOW, online_game_rect)
    screen.blit(text, (online_game_rect.centerx - text.get_width() / 2, online_game_rect.centery - text.get_height() / 2))
    rectangles[ONLINE_GAME] = online_game_rect

    rectangles[NUMBER_OF_PLAYERS] = create_players_count_rects()

    rectangles[GAME_LENGTH] = create_small_rects("GAME_LENGTH", GAME_LENGTH_OPTION, default=game_length,
                                           color=colors.DARK_RED, chosen_color=colors.RED, is_left=True)

    rectangles[BOT_LEVEL] = create_small_rects("BOT LEVEL", range(1, 5), default=level,
                                         color=colors.DARK_BLUE, chosen_color=colors.LIGHT_BLUE, is_left=False)

    # Passing the 'one player' rect as argument to the function.
    rectangles[TEAM_SELECTION] = draw_team_selection_rects(rectangles[NUMBER_OF_PLAYERS]["One Player"].midright, is_white)
    rectangles[PIECES_SET] = draw_pieces_set_selection_rects()
    rectangles[BOARD_SET] = draw_board_set_selection_rects()



    return rectangles


def draw_board_set_selection_rects():
    rects = dict()
    current_print_height = 500
    pieces_set_one = pygame.Rect(RECT_WIDTH , current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.LIGHT_SILVER, pieces_set_one)
    text = "BOARD SET 1"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (pieces_set_one.centerx - text_surface.get_width() / 2,
                               pieces_set_one.centery - text_surface.get_height() / 2))
    current_print_height += 200
    rects[text] = pieces_set_one

    pieces_set_two = pygame.Rect(RECT_WIDTH , current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.DARK_SILVER, pieces_set_two)
    text = "BOARD SET 2"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (pieces_set_two.centerx - text_surface.get_width() / 2,
                               pieces_set_two.centery - text_surface.get_height() / 2))
    rects[text] = pieces_set_two
    return rects


def handle_event(event, rectangles):
    if event.type == pygame.QUIT:
        raise exceptions.UserExitGame

    elif event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = pygame.mouse.get_pos()

        try:
            rect_group, rect_clicked, text_in_rect = get_rect(mouse_pos, rectangles)
            return rect_group_to_function[rect_group](rect_clicked, text_in_rect, rectangles)

        # The user clicked on something that not the rect
        except exceptions.NonReturnValue:
            pass


def get_rect(mouse_pos, rectangles):
    for rect_group in rectangles:

        if rect_group in ONE_RECT_GROUPS:
            rect = rectangles[rect_group]
            if rect.collidepoint(*mouse_pos):
                return rect_group, rect, None

        else:
            rects = rectangles[rect_group]
            for text in rects:
                rect = rects[text]
                if rect.collidepoint(*mouse_pos):
                    return rect_group, rect, text

    raise exceptions.NonReturnValue


def join_to(rect_clicked, game: WaitingGame, rectangles):
    final_request = protocol.Request(username, protocol.JOIN_GAME, game.opponent_player_name).set_request_to_server()
    my_socket.send(final_request)
    if my_socket.recv(1) == protocol.OK_MESSAGE:
        global is_white
        global opponent_player_name
        global game_length
        is_white = game.is_white
        game_length = game.length
        opponent_player_name = game.opponent_player_name
        raise exceptions.FinishStartingScreen
    else:
        raise exceptions.JoinGameError


def set_team(rect_clicked, text, rectangles):
    if not is_one_players_playing:
        return
    global is_white
    is_white = True if text == "WHITE TEAM" else False
    set_rects_color(rectangles[TEAM_SELECTION], rect_clicked,
                       colors.LIGHT_SILVER, colors.DARK_SILVER, colors.BLACK)
    




def back_to_last_screen(*ignore):
    raise exceptions.BackToLastScreen


def finish_starting_screen(*ignore):
    raise exceptions.FinishStartingScreen


def set_number_of_players(rect_clicked, text, rectangles):
    global is_one_players_playing
    global game_type
    is_one_players_playing = (text == 'One Player')

    if is_one_players_playing:
        # Passing the 'one player' rect as argument to the function.
        draw_team_selection_rects(rectangles[NUMBER_OF_PLAYERS]["One Player"].midright, is_white)
        game_type = BOT_GAME_TYPE
    else:
        # Erase team selection rectangles.
        screen.blit(bg_image, rectangles[TEAM_SELECTION]["WHITE TEAM"].topleft,
                    rectangles[TEAM_SELECTION]["WHITE TEAM"])
        screen.blit(bg_image, rectangles[TEAM_SELECTION]["BLACK TEAM"].topleft,
                    rectangles[TEAM_SELECTION]["BLACK TEAM"])
        game_type = TWO_PLAYERS_GAME_TYPE

    set_rects_color(rectangles[NUMBER_OF_PLAYERS], rect_clicked,
                       colors.LIGHT_SILVER, colors.DARK_SILVER, colors.BLACK)
    

def set_bot_level(rect_clicked, text, rectangles):
    global level
    level = int(text)
    set_rects_color(rectangles[BOT_LEVEL], rect_clicked, colors.LIGHT_BLUE, colors.DARK_BLUE)


def set_game_length(rect_clicked, text, rectangles):
    global game_length
    game_length = int(text)
    set_rects_color(rectangles[GAME_LENGTH], rect_clicked, colors.RED, colors.DARK_RED)

def set_board(rect_clicked, text, rectangles):
    global is_board_set_one
    is_board_set_one = True if text == "BOARD SET 1" else False
    set_rects_color(rectangles[BOARD_SET], rect_clicked,
                       colors.LIGHT_SILVER, colors.DARK_SILVER, colors.BLACK)
    
    
def create_small_rects(title, options, default, color, chosen_color, is_left):
    # Draw the rectangles in the sides of the starting screen.
    # Return a dictionary. the key is the text and the value is the rect.

    rects = {}
    current_print_height = 100
    x_pos = 5 if is_left else (SCREEN_WIDTH - SMALL_RECT_WIDTH - 5)
    for option in options:
        # Set the color of the rect. the chosen option is in other color.
        rect_color = chosen_color if option == default else color
        rect = pygame.Rect(x_pos, current_print_height, SMALL_RECT_WIDTH,
                           SMALL_RECT_HEIGHT)
        pygame.draw.rect(screen, rect_color, rect)
        # print the text in rect
        text = f"{option}"
        text_surface = REGULAR_FONT.render(text, False, colors.WHITE)
        screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2
                                   , rect.centery - text_surface.get_height() / 2))
        rects[text] = rect
        current_print_height += (SMALL_RECT_HEIGHT * 2)

    # Print title.
    text_surface = REGULAR_FONT.render(title, True, color)
    if is_left:
        screen.blit(text_surface,
                    (max(rect.centerx - text_surface.get_width() / 2, 0), 10))  # Space from top.
    else:
        screen.blit(text_surface,
                    (min(rect.centerx - text_surface.get_width() / 2, SCREEN_WIDTH - text_surface.get_width() - 10),
                     10))  # Space from top.
    return rects


def create_players_count_rects():
    # Return a dictionary. the key is the text and the value is the rect.

    rects = dict()
    current_print_height = 150
    one_player_rect = pygame.Rect(MIDDLE_HORIZONTAL - RECT_WIDTH / 2, current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.LIGHT_SILVER, one_player_rect)
    text = "One Player"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (one_player_rect.centerx - text_surface.get_width() / 2,
                               one_player_rect.centery - text_surface.get_height() / 2))
    current_print_height += 200
    rects[text] = one_player_rect

    two_player_rect = pygame.Rect(MIDDLE_HORIZONTAL - RECT_WIDTH / 2, current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.DARK_SILVER, two_player_rect)
    text = "Two Players"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (two_player_rect.centerx - text_surface.get_width() / 2,
                               two_player_rect.centery - text_surface.get_height() / 2))
    rects[text] = two_player_rect
    return rects


def draw_team_selection_rects(one_player_rect_cords, isWhite=True):
    x_pos, y_pos = one_player_rect_cords
    x_pos += SCREEN_WIDTH / 10
    white_team_y_pos = y_pos - SCREEN_WIDTH / 20
    black_team_y_pos = y_pos + SCREEN_WIDTH / 20
    white_team_color, black_team_color = (colors.LIGHT_SILVER, colors.DARK_SILVER) if isWhite else \
        (colors.DARK_SILVER, colors.LIGHT_SILVER)
    rects = {}
    rect = pygame.Rect(x_pos, white_team_y_pos, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, white_team_color, rect)
    text = "WHITE TEAM"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2,
                               rect.centery - text_surface.get_height() / 2))
    rects[text] = rect

    rect = pygame.Rect(x_pos, black_team_y_pos, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, black_team_color, rect)
    text = "BLACK TEAM"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2,
                               rect.centery - text_surface.get_height() / 2))
    rects[text] = rect
    return rects


def draw_pieces_set_selection_rects():
    rects = dict()
    current_print_height = 150
    pieces_set_one = pygame.Rect(RECT_WIDTH , current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.LIGHT_SILVER, pieces_set_one)
    text = "PIECES SET 1"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (pieces_set_one.centerx - text_surface.get_width() / 2,
                               pieces_set_one.centery - text_surface.get_height() / 2))
    current_print_height += 200
    rects[text] = pieces_set_one

    pieces_set_two = pygame.Rect(RECT_WIDTH , current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.DARK_SILVER, pieces_set_two)
    text = "PIECES SET 2"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (pieces_set_two.centerx - text_surface.get_width() / 2,
                               pieces_set_two.centery - text_surface.get_height() / 2))
    rects[text] = pieces_set_two
    return rects


def set_rects_color(rects_and_texts: dict, chosen_rect, chosen_rect_color, unchosen_rect_color,
                       text_color=colors.WHITE):
    for text, rect in rects_and_texts.items():
        color = chosen_rect_color if rect is chosen_rect else unchosen_rect_color
        pygame.draw.rect(screen, color, rect)
        text_surface = REGULAR_FONT.render(text, False, text_color)
        if rect.width == RECT_WIDTH:
            screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2,
                                       rect.centery - text_surface.get_height() / 2))
        else:
            screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2,
                                       rect.centery - text_surface.get_height() / 2))


def draw_and_get_back_button():
    back_button_x_pos = 0
    back_button_y_pos = SCREEN_HEIGHT - back_button_image.get_height() - 20
    screen.blit(back_button_image, (back_button_x_pos, back_button_y_pos))
    tmp_rect = back_button_image.get_rect()
    tmp_rect.topleft = (back_button_x_pos, back_button_y_pos)
    return tmp_rect


def draw_and_get_refresh_button():
    refresh_button_x_pos = SCREEN_WIDTH - refresh_button_image.get_width()
    refresh_button_y_pos = SCREEN_HEIGHT - refresh_button_image.get_height() - 20
    screen.blit(refresh_button_image, (refresh_button_x_pos, refresh_button_y_pos))
    return pygame.Rect(refresh_button_x_pos, refresh_button_y_pos,
                       refresh_button_image.get_width(), refresh_button_image.get_width())


def set_pieces(rect_clicked, text, rectangles):
    global is_pieces_set_one
    is_pieces_set_one = True if text == "PIECES SET 1" else False
    set_rects_color(rectangles[PIECES_SET], rect_clicked, colors.LIGHT_SILVER, colors.DARK_SILVER, colors.BLACK)


rect_group_to_function = dict()
rect_group_to_function[START_GAME] = finish_starting_screen
rect_group_to_function[NUMBER_OF_PLAYERS] = set_number_of_players
rect_group_to_function[GAME_LENGTH] = set_game_length
rect_group_to_function[BOT_LEVEL] = set_bot_level
rect_group_to_function[TEAM_SELECTION] = set_team
rect_group_to_function[ONLINE_GAME] = online_screen
rect_group_to_function[BACK_BUTTON] = back_to_last_screen
rect_group_to_function[JOIN_GAME_RECTS] = join_to
rect_group_to_function[REFRESH_BUTTON] = join_game_screen
rect_group_to_function[PIECES_SET] = set_pieces
rect_group_to_function[BOARD_SET] = set_board


