import os

import chess
import chess.pgn
from io import StringIO
from stockfish import Stockfish
from ansi_colours import AnsiColours as Colour
from tabulate import tabulate
import pygame

################################################# STOCKFISH SETTINGS ###################################################
fish = Stockfish("/home/michael/PycharmProjects/GameReview/stockfish-ubuntu-x86-64-avx2")
depth = 16

################################################### CHESS SETTINGS #####################################################
pgn = "game.pgn"
board = chess.Board()

###################################################### FUNCTIONS #######################################################


def read_pgn():
    return chess.pgn.read_game(StringIO(open(pgn).read()))


def get_pgn_information(opened):
    headers = opened.headers
    headers_list = [headers["Date"], headers["White"], headers["WhiteElo"], headers["Black"], headers["BlackElo"], headers["Termination"]]
    return headers_list


def move_information_dictionary():
    return {
        "great": 0,
        "excellent": 0,
        "good": 0,
        "inaccuracies": 0,
        "miss": 0,
        "blunder": 0
    }


def calculate_mate_score(evaluation_value, is_white_move):
    if evaluation_value == 0:
        return -1 if not is_white_move else 1
    return -1 if evaluation_value < 0 else 1


def get_san(fen, coord_move):
    board2 = chess.Board()
    board2.set_fen(fen)
    move2 = chess.Move.from_uci(coord_move)
    return board.san(move2)

#################################################### MAIN PROGRAM ######################################################
opened_pgn = read_pgn()
information = get_pgn_information(opened_pgn)
white_evaluations = move_information_dictionary()
black_evaluations = move_information_dictionary()
bad_move_fens = {}
last_cp = 0
evaluated = []
best_moves = []
san_move_list = []

n_moves = 0
moves = []
for move in opened_pgn.mainline_moves():
    n_moves += 1
    moves.append(move)

for i, move in enumerate(opened_pgn.mainline_moves()):
    print(f"Calculating Move {i+1}/{n_moves}")
    evaluation = fish.get_evaluation()
    cp = evaluation["value"]
    top_moves = fish.get_top_moves(num_top_moves=5)
    best_move = get_san(board.fen(), top_moves[0]['Move'])
    board.push_san(best_move)
    best_cp = fish.get_evaluation()["value"]/100
    board.pop()
    great_moves = []
    excellent_moves = []
    for move2 in top_moves:
        san = get_san(board.fen(), move2['Move'])
        top_cp = move2["Centipawn"]
        if top_cp is None:
            excellent_moves.append(san)
        elif top_cp - cp <= 10:
            excellent_moves.append(san)
        elif top_cp - cp > 10:
            great_moves.append(san)

    current_turn = True if i % 2 == 1 else False
    move_number = (i+1 // 2)+1
    san_move_list.append(get_san(board.fen(), str(move).removeprefix("chess.Move.from_uci('").removesuffix("')")))

    san = board.san(move)
    board.push(move)
    last_cp = cp
    fish.set_fen_position(board.fen())
    evaluation = fish.get_evaluation()
    cp = evaluation["value"]
    evaltype = evaluation["type"]
    delta = (cp-last_cp)/100

    if current_turn:
        if best_move == san:
            evaluated.append("be")
            best_moves.append(Colour.cyan(f"Best Move! That was the best possible move you could have played!"))
        elif delta <= -3:
            evaluated.append("bl")
            best_moves.append(Colour.red(f"You blundered and lost {abs(delta)} centipawns! The best move was {best_move}, which would have {'gained' if best_cp >= 0 else 'lost'} {abs(best_cp)} centipawns."))
        elif delta <= -1.5:
            evaluated.append("in")
            best_moves.append(Colour.yellow(f"You inaccurately moved a piece and lost {abs(delta)} centipawns! The best move was {best_move}, which would have {'gained' if best_cp >= 0 else 'lost'} {abs(best_cp)} centipawns."))
        elif delta <= -0.5:
            evaluated.append("m")
            best_moves.append(Colour.yellow(f"You missed a good move and lost {abs(delta)} centipawns! The best move was {best_move}, which would have {'gained' if best_cp >= 0 else 'lost'} {abs(best_cp)} centipawns."))
        elif delta <= 1:
            evaluated.append("e")
            best_moves.append(Colour.green(f"Excellent Move! This move {'gained' if best_cp >= 0 else 'lost'} {abs(delta)} centipawns, but the best move was {best_move}, which would have {'gained' if best_cp >= 0 else 'lost'} {abs(best_cp)} centipawns."))
        elif delta > 1:
            evaluated.append("g")
            best_moves.append(Colour.blue(f"Great Move! This move gained {abs(delta)} centipawns, but the best move was {best_move}, which would have {'gained' if best_cp >= 0 else 'lost'} {abs(best_cp)} centipawns."))
    else:
        if best_move == san:
            evaluated.append("be")
            best_moves.append(Colour.cyan(f"Best Move! That was the best possible move you could have played!"))
        elif delta <= -3:
            evaluated.append("bl")
            best_moves.append(Colour.red(f"You blundered and lost {abs(delta)} centipawns! The best move was {best_move}, which would have {'lost' if best_cp >= 0 else 'gained'} {abs(best_cp)} centipawns."))
        elif delta <= -1.5:
            evaluated.append("in")
            best_moves.append(Colour.yellow(f"You inaccurately moved a piece and lost {abs(delta)} centipawns! The best move was {best_move}, which would have {'lost' if best_cp >= 0 else 'gained'} {abs(best_cp)} centipawns."))
        elif delta <= -0.5:
            evaluated.append("m")
            best_moves.append(Colour.yellow(f"You missed a good move and lost {abs(delta)} centipawns! The best move was {best_move}, which would have {'lost' if best_cp >= 0 else 'gained'} {abs(best_cp)} centipawns."))
        elif delta <= 1:
            evaluated.append("e")
            best_moves.append(Colour.green(f"Excellent Move! This move {'lost' if best_cp >= 0 else 'gained'} {abs(delta)} centipawns, but the best move was {best_move}, which would have {'lost' if best_cp >= 0 else 'gained'} {abs(best_cp)} centipawns."))
        elif delta > 1:
            evaluated.append("g")
            best_moves.append(Colour.blue(f"Great Move! This move gained {abs(delta)} centipawns, but the best move was {best_move}, which would have gained {abs(best_cp)} centipawns."))

san_white = []
san_black = []

for i in range(len(evaluated)):
    if i % 2 == 0:
        if evaluated[i] == "bl":
            san_white.append(Colour.red(f"{san_move_list[i]} (Blunder)"))
        if evaluated[i] == "be":
            san_white.append(Colour.cyan(f"{san_move_list[i]} (Best Move)"))
        if evaluated[i] == "in":
            san_white.append(Colour.yellow(f"{san_move_list[i]} (Inaccuracy)"))
        if evaluated[i] == "m":
            san_white.append(Colour.yellow(f"{san_move_list[i]} (Miss)"))
        if evaluated[i] == "e":
            san_white.append(Colour.green(f"{san_move_list[i]} (Excellent Move)"))
        if evaluated[i] == "g":
            san_white.append(Colour.blue(f"{san_move_list[i]} (Great Move)"))
    else:
        if evaluated[i] == "bl":
            san_black.append(Colour.red(f"{san_move_list[i]} (Blunder)"))
        if evaluated[i] == "be":
            san_black.append(Colour.cyan(f"{san_move_list[i]} (Best Move)"))
        if evaluated[i] == "in":
            san_black.append(Colour.yellow(f"{san_move_list[i]} (Inaccuracy)"))
        if evaluated[i] == "m":
            san_black.append(Colour.yellow(f"{san_move_list[i]} (Miss)"))
        if evaluated[i] == "e":
            san_black.append(Colour.green(f"{san_move_list[i]} (Excellent Move)"))
        if evaluated[i] == "g":
            san_black.append(Colour.blue(f"{san_move_list[i]} (Great Move)"))

san_combined = []
error_encountered = False

for i in range(len(san_white)):
    try:
        white_move = san_white[i]
        black_move = san_black[i]
        san_combined.append([f"{i+1}. ", white_move, black_move])
    except IndexError:
        san_combined.append([f"{i+1}. ", white_move, "1-0"])
        error_encountered = True

if not error_encountered:
    san_combined.append([f"{len(san_combined)+1}. ", "0-1"])

print(tabulate(san_combined, ["Move", "White", "Black"]))
pygame.init()
scale = pygame.display.Info().current_w/1920
app = pygame.display.set_mode((650*scale, 512*scale))

def load_piece(name: str):
    return pygame.transform.scale(pygame.image.load("pieces/" + name), (64*scale, 64*scale)).convert_alpha(), pygame.transform.scale(pygame.image.load(f"pieces/{name.removesuffix('.png')}2.png"), (64*scale, 64*scale)).convert_alpha()

pawn, pawn2 = load_piece("pawn.png")
knight, knight2 = load_piece("knight.png")
bishop, bishop2 = load_piece("bishop.png")
rook, rook2 = load_piece("rook.png")
queen, queen2 = load_piece("queen.png")
king, king2 = load_piece("king.png")
green = pygame.transform.scale(pygame.image.load("green.png"), (64*scale, 64*scale))
white = pygame.transform.scale(pygame.image.load("white.png"), (64*scale, 64*scale))

def load_annotation(name):
    return pygame.transform.scale(pygame.image.load(os.path.join("128x", name)), (32*scale, 32*scale))

blunder = load_annotation("blunder_128x.png")
brilliant = load_annotation("brilliant_128x.png")
mistake = load_annotation("mistake_128x.png")
excellent = load_annotation("excellent_128x.png")
inaccuracy = load_annotation("inaccuracy_128x.png")
great = load_annotation("great_find_128x.png")

def draw_board():
    green_square = False
    for i in range(8):
        for i2 in range(8):
            if green_square:
                app.blit(green, (i2*64*scale, i*64*scale))
                green_square = False
            else:
                app.blit(white, (i2*64*scale, i*64*scale))
                green_square = True
        if green_square:
            green_square = False
        else:
            green_square = True

def draw_pieces(board3):
    pieces = {
        "R": rook2,
        "N": knight2,
        "P": pawn2,
        "B": bishop2,
        "Q": queen2,
        "K": king2,
        "r": rook,
        "n": knight,
        "p": pawn,
        "b": bishop,
        "q": queen,
        "k": king,
    }

    x = 0
    y = 0
    for i in range(8):
        for i2 in range(8):
            if board3.piece_at((i*8)+i2) is not None:
                square = i * 8 + i2
                piece = str(board3.piece_at(square)).removesuffix("')").removeprefix("Piece.from_symbol('")
                app.blit(pieces[piece], (x, y))
            x += 64*scale
        y += 64*scale
        x = 0
    
def add_annotation(x, y, name):
    if name == "bl":
        app.blit(blunder, (x+(32*scale), y-(32*scale)))
    if name == "be":
        app.blit(brilliant, (x + (32 * scale), y - (32 * scale)))
    if name == "g":
        app.blit(great, (x + (32 * scale), y - (32 * scale)))
    if name == "in":
        app.blit(inaccuracy, (x + (32 * scale), y - (32 * scale)))
    if name == "m":
        app.blit(mistake, (x + (32 * scale), y - (32 * scale)))
    if name == "e":
        app.blit(excellent, (x + (32 * scale), y - (32 * scale)))

def calculate_real_move(move: str):
    move2 = move.removesuffix("')").removeprefix("Move.from_uci('")
    letters = list("abcdefgh")
    parts = list(move2)
    part1 = letters[7-letters.index(parts[0])]
    part2 = letters[7-letters.index(parts[2])]
    return str(part1 + parts[1] + part2 + parts[3])


def get_coords_from_square(square: str):
    square = list(square)
    letters = list("abcdefgh")
    x = letters.index(square[0])*(64*scale)
    y = (int(square[1])-0.5)*(64*scale)
    return x, y


running = True
move_number = 0
board4 = chess.Board()

while running:
    app.fill((255, 255, 255))
    draw_board()
    draw_pieces(board4)
    if move_number > 0:
        move5 = list(str(moves[move_number-1]).removeprefix("chess.Move.from_uci('").removesuffix("')"))
        x2, y2 = get_coords_from_square(move5[2] + move5[3])
        add_annotation(x2, y2, evaluated[move_number-1])
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and move_number > 0:
                board4.pop()
                move_number -= 1
            if event.key == pygame.K_RIGHT and move_number < len(san_move_list):
                move_number += 1
                board4.push(moves[move_number-1])
    pygame.display.flip()