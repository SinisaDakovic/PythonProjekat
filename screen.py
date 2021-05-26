import pygame
import colors
from teams import Team, get_score_difference
import os
import exceptions

pygame.init()

SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h
HEIGHT_OF_SCOREBOARD = 200

SPACE_FROM_BOARD = 50
BOARD_SIDE = SCREEN_HEIGHT-HEIGHT_OF_SCOREBOARD - SPACE_FROM_BOARD*2

MIDDLE_HORIZONTAL = SCREEN_WIDTH / 2
RECT_WIDTH = 200
RECT_HEIGHT = 100

NUMBER_OF_SMALL_RECTS = 4
SMALL_RECT_WIDTH = SCREEN_WIDTH/(NUMBER_OF_SMALL_RECTS*4)
SMALL_RECT_HEIGHT = SCREEN_HEIGHT/(NUMBER_OF_SMALL_RECTS*2)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

squares = []
PICTURES_PATH = 'pictures'

NUMBER_OF_SQUARES = 8
SCORE_BOARD = pygame.Surface((SCREEN_WIDTH, HEIGHT_OF_SCOREBOARD))
REGULAR_FONT = pygame.font.SysFont('comicsansms', 30)
LARGE_FONT = pygame.font.Font('freesansbold.ttf', 40)

GAME_LENGTH_OPTION = (1, 3, 5, 10)


class Square:
    SIDE = BOARD_SIDE/NUMBER_OF_SQUARES

    def __init__(self, x, y, color, tur, line):
        self.rect = pygame.Rect(x, y, self.SIDE, self.SIDE)
        self.color = color
        self.original_color = color
        self.tur_cord = tur
        self.line_cord = line
        self.x_mid = x + Square.SIDE/2
        self.y_mid = y + Square.SIDE/2
        self.current_piece = None

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        if self.current_piece is not None:
            self.current_piece.draw()

    def coloring_square_by_original_color(self):
        if self.color == self.original_color:
            if self.original_color == colors.DARK_BROWN:
                self.color = colors.DARK_RED
            else:
                self.color = colors.LIGHT_RED
        else:
            self.color = self.original_color

    def __str__(self):
        return f'(line: {self.line_cord}, tur: {self.tur_cord})'


def add_squares_to_board():
    # at the begging of the game, draw and init the squares.

    bg_image = pygame.image.load(os.path.join(PICTURES_PATH, 'main_background.jpg'))
    screen.blit(bg_image, (0, HEIGHT_OF_SCOREBOARD))

    x = SPACE_FROM_BOARD
    y = HEIGHT_OF_SCOREBOARD + SPACE_FROM_BOARD
    for line in range(NUMBER_OF_SQUARES):
        tmp = line % 2
        square_in_line = []
        for tur in range(NUMBER_OF_SQUARES):
            if tur % 2 == tmp:
                color = colors.LIGHT_BROWN
            else:
                color = colors.DARK_BROWN

            square_in_line.append(Square(x, y, color, tur, line))
            x += Square.SIDE
        x = SPACE_FROM_BOARD
        y += Square.SIDE
        squares.append(square_in_line)
    pygame.display.flip()


def is_move_to_square_valid(tur, line, team):
    if 0 <= line < NUMBER_OF_SQUARES and 0 <= tur < NUMBER_OF_SQUARES:
        # Square is on the board
        check_square_piece = squares[line][tur].current_piece
        if check_square_piece is not None:
            # Check if other piece is on the same team.
            return team is not check_square_piece.team
        # Next move is inside board and empty square.
        return True
    return False


def draw_bg(team_got_turn: Team, team_doesnt_got_turn: Team):
    draw_scoreboard(team_got_turn, team_doesnt_got_turn)
    draw_board()


def draw_scoreboard(team_got_turn: Team, team_doesnt_got_turn: Team):
    white_team = team_got_turn if team_got_turn.is_white_team else team_doesnt_got_turn
    black_team = team_got_turn if not team_got_turn.is_white_team else team_doesnt_got_turn

    screen.blit(SCORE_BOARD, (0, 0))
    # I switched to just clear color and not an image as the background of the scoreboard.
    # draw bg image of score board. this way the last "scoreboard" is erased.
    SCORE_BOARD.fill(colors.DARK_BLUE)
    # bg_image = pygame.image.load(os.path.join(PICTURES_PATH, 'boardscore_bg.png'))
    # SCORE_BOARD.blit(bg_image, (0, 0))

    draw_who_turn_is(team_got_turn)
    draw_timers(white_team, black_team)
    draw_score(team_got_turn, team_doesnt_got_turn)


def draw_board():
    for line in squares:
        for square in line:
            square.draw()


def draw_who_turn_is(team_got_turn):
    if team_got_turn.is_white_team:
        text = LARGE_FONT.render('White Player Turn', False, colors.WHITE)
    else:
        text = LARGE_FONT.render('Black Player Turn', False, colors.BLACK)

    SCORE_BOARD.blit(text, (SCORE_BOARD.get_width() / 2 - 170, 0))


def draw_timer(team):
    timer = team.timer
    color = colors.WHITE if team.is_white_team else colors.BLACK
    minutes = timer.get_minutes_left()
    seconds = timer.get_seconds_left_to_last_minute()
    if seconds == 60:
        seconds = '00'
    seconds = str(seconds).zfill(2)
    minutes = str(minutes).zfill(2)
    text = REGULAR_FONT.render(f"{minutes}:{seconds}", False, color)
    place = (10, 0) if team.is_white_team else (SCORE_BOARD.get_width() - text.get_width(), 0)
    SCORE_BOARD.blit(text, place)


def draw_timers(white_team, black_team):
    draw_timer(white_team)
    draw_timer(black_team)


def draw_score(team_got_turn, team_doesnt_got_turn):
    white_team = team_got_turn if team_got_turn.is_white_team else team_doesnt_got_turn
    black_team = team_got_turn if not team_got_turn.is_white_team else team_doesnt_got_turn

    white_team.update_score()
    black_team.update_score()

    length = SCREEN_WIDTH - 20
    text = REGULAR_FONT.render("White team score:", False, colors.WHITE)
    SCORE_BOARD.blit(text, (0, SCORE_BOARD.get_height() - 15 - text.get_height()))

    text = REGULAR_FONT.render("Black team score:", False, colors.WHITE)
    SCORE_BOARD.blit(text, (SCREEN_WIDTH - text.get_width() - 10, SCORE_BOARD.get_height() - 15 - text.get_height()))

    pygame.draw.rect(SCORE_BOARD, colors.BLACK, (10, SCORE_BOARD.get_height() - 15, length, 10))
    white_rect_length = length / 2 + get_score_difference(white_team, black_team) / 10
    pygame.draw.rect(SCORE_BOARD, colors.WHITE, (10, SCORE_BOARD.get_height() - 15, white_rect_length, 10))


def color_all_square_to_original_color():
    for line in squares:
        for square in line:
            if square.color != square.original_color:
                square.coloring_square_by_original_color()


def starting_screen():
    is_one_players_playing = True
    game_length = 5  # In minutes.
    level = 3  # Depth

    # Print background image.
    bg_image = pygame.image.load(os.path.join(PICTURES_PATH, 'opening_screen_picture.png'))
    screen.blit(bg_image, (0, 0))
    # Print title.
    text = LARGE_FONT.render("BeCheZ", False, colors.YELLOW)
    screen.blit(text, (SCREEN_WIDTH / 2 - text.get_width()/2, 50))
    # Print start game rect.
    start_game_rect = pygame.Rect(MIDDLE_HORIZONTAL - RECT_WIDTH / 2, 550, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.YELLOW, start_game_rect)
    text = REGULAR_FONT.render("Start Game", False, colors.BLACK)
    screen.blit(text, (start_game_rect.centerx - text.get_width()/2, start_game_rect.centery - text.get_height()/2))

    number_of_players_rects = create_players_count_rects()
    game_length_rects = create_game_length_rects(GAME_LENGTH_OPTION, default_minutes=5)
    bot_level_rects = create_bot_levels_rects(default_level=3)
    while True:
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise exceptions.UserExitGame

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if start_game_rect.collidepoint(*mouse_pos):
                    return is_one_players_playing, game_length, level

                for text, rect in number_of_players_rects.items():
                    if rect.collidepoint(*mouse_pos):
                        is_one_players_playing = (text == 'One Player')
                        draw_other_rects_in_other_color(number_of_players_rects, rect,
                                                        colors.LIGHT_SILVER, colors.DARK_SILVER, colors.BLACK)

                for text, rect in game_length_rects.items():
                    if rect.collidepoint(*mouse_pos):
                        game_length = int(text)
                        draw_other_rects_in_other_color(game_length_rects, rect, colors.RED, colors.DARK_RED)

                for text, rect in bot_level_rects.items():
                    if rect.collidepoint(*mouse_pos):
                        level = int(text)
                        draw_other_rects_in_other_color(bot_level_rects, rect, colors.LIGHT_BLUE, colors.DARK_BLUE)


def create_bot_levels_rects(default_level):
    bot_level_rects = {}
    current_print_height = 100
    for bot_level in range(1, 5):
        color = colors.LIGHT_BLUE if bot_level == default_level else colors.DARK_BLUE
        rect = pygame.Rect(SCREEN_WIDTH - SMALL_RECT_WIDTH - 5, current_print_height, SMALL_RECT_WIDTH, SMALL_RECT_HEIGHT)
        pygame.draw.rect(screen, color, rect)
        text = f"{bot_level}"
        text_surface = REGULAR_FONT.render(text, False, colors.WHITE)
        screen.blit(text_surface, (rect.centerx - 5, rect.centery - 5))
        bot_level_rects[text] = rect
        current_print_height += (SMALL_RECT_HEIGHT * 2)

    text_surface = REGULAR_FONT.render('Bot Level', True, colors.DARK_BLUE)
    screen.blit(text_surface, (min(rect.centerx - text_surface.get_width()/2, SCREEN_WIDTH - text_surface.get_width() - 10),
                               10)) # Space from top.
    return bot_level_rects


def create_game_length_rects(minutes_options, default_minutes):
    # Return a dictionary. the key is the text and the value is the rect.

    game_length_rects = {}

    current_print_height = 100
    for minute in minutes_options:
        color = colors.RED if minute == default_minutes else colors.DARK_RED
        text = f"{minute}"
        rect = pygame.Rect(10, current_print_height, SMALL_RECT_WIDTH, SMALL_RECT_HEIGHT)
        pygame.draw.rect(screen, color, rect)
        text_surface = REGULAR_FONT.render(text, False, colors.WHITE)
        screen.blit(text_surface, (rect.centerx - text_surface.get_width()/2,
                                   rect.centery - text_surface.get_height()/2))
        current_print_height += (SMALL_RECT_HEIGHT*2)
        game_length_rects[text] = rect

    text_surface = REGULAR_FONT.render('Game Length', True, colors.DARK_RED)
    screen.blit(text_surface, (max(rect.centerx - text_surface.get_width()/2, 0),
                               10)) # Space from top.
    return game_length_rects


def create_players_count_rects():
    # Return a dictionary. the key is the text and the value is the rect.

    number_of_players_rects = {}
    current_print_height = 150
    one_player_rect = pygame.Rect(MIDDLE_HORIZONTAL - RECT_WIDTH / 2, current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.LIGHT_SILVER, one_player_rect)
    text = "One Player"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (one_player_rect.centerx - text_surface.get_width()/2,
                               one_player_rect.centery - text_surface.get_height()/2))
    current_print_height += 200
    number_of_players_rects[text] = one_player_rect

    two_player_rect = pygame.Rect(MIDDLE_HORIZONTAL - RECT_WIDTH / 2, current_print_height, RECT_WIDTH, RECT_HEIGHT)
    pygame.draw.rect(screen, colors.DARK_SILVER, two_player_rect)
    text = "Two Players"
    text_surface = REGULAR_FONT.render(text, False, colors.BLACK)
    screen.blit(text_surface, (two_player_rect.centerx - text_surface.get_width()/2,
                               two_player_rect.centery - text_surface.get_height()/2))
    number_of_players_rects[text] = two_player_rect
    return number_of_players_rects


def draw_other_rects_in_other_color(rects_and_texts: dict, chosen_rect, chosen_rect_color, unchosen_rect_color,
                                    text_color=colors.WHITE):
    for text, rect in rects_and_texts.items():
        color = chosen_rect_color if rect is chosen_rect else unchosen_rect_color
        pygame.draw.rect(screen, color, rect)
        text_surface = REGULAR_FONT.render(text, False, text_color)
        if rect.width == RECT_WIDTH:
            screen.blit(text_surface, (rect.centerx - text_surface.get_width()/2,
                                       rect.centery - text_surface.get_height()/2))
        else:
            screen.blit(text_surface, (rect.centerx - text_surface.get_width()/2,
                                       rect.centery - text_surface.get_height()/2))


def draw_winner(team_won):
    text = f"Team won is {team_won}"
    text_surface = LARGE_FONT.render(text, False, colors.LIGHT_BLUE)
    screen.blit(text_surface, (SCREEN_WIDTH / 2 - 235, SCREEN_HEIGHT / 2 - 30))
    pygame.display.flip()


def draw_tie():
    text = f"Tie"
    text_surface = screen.LARGE_FONT.render(text, False, colors.DARK_GREEN)
    screen.screen.blit(text_surface, (screen.SCREEN_WIDTH / 2 - 50, screen.SCREEN_HEIGHT / 2 - 30))
    pygame.display.flip()
