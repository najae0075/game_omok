import random

import streamlit as st

SIZE = 15
EMPTY = 0
USER = 1
AI = 2
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]


def new_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def is_valid_move(board, row, col):
    return 0 <= row < SIZE and 0 <= col < SIZE and board[row][col] == EMPTY


def count_direction(board, row, col, dr, dc, player):
    count = 1

    r = row + dr
    c = col + dc
    while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
        count += 1
        r += dr
        c += dc

    r = row - dr
    c = col - dc
    while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
        count += 1
        r -= dr
        c -= dc

    return count


def check_win(board, row, col, player):
    for dr, dc in DIRECTIONS:
        if count_direction(board, row, col, dr, dc, player) >= 5:
            return True
    return False


def get_candidate_moves(board):
    moves = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != EMPTY:
                continue
            score = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr = r + dr
                    cc = c + dc
                    if 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] != EMPTY:
                        score += 1
            center_distance = abs(r - SIZE // 2) + abs(c - SIZE // 2)
            score += max(0, 5 - center_distance)
            moves.append((score, r, c))
    moves.sort(reverse=True)
    return moves


def evaluate_position(board, row, col, player):
    total = 0
    for dr, dc in DIRECTIONS:
        length = count_direction(board, row, col, dr, dc, player)
        if length >= 5:
            total += 100000
        elif length == 4:
            total += 1000
        elif length == 3:
            total += 120
        elif length == 2:
            total += 10
        elif length == 1:
            total += 1
    return total


def choose_ai_move(board, difficulty):
    candidate_moves = get_candidate_moves(board)
    if not candidate_moves:
        return None

    if difficulty == "easy":
        _, r, c = random.choice(candidate_moves)
        return r, c

    winning_moves = []
    for _, r, c in candidate_moves:
        if not is_valid_move(board, r, c):
            continue
        board[r][c] = AI
        if check_win(board, r, c, AI):
            winning_moves.append((r, c))
        board[r][c] = EMPTY

    if winning_moves:
        return winning_moves[0]

    blocking_moves = []
    for _, r, c in candidate_moves:
        if not is_valid_move(board, r, c):
            continue
        board[r][c] = USER
        if check_win(board, r, c, USER):
            blocking_moves.append((r, c))
        board[r][c] = EMPTY

    if blocking_moves:
        return blocking_moves[0]

    if difficulty == "normal":
        best_score = -10**9
        best_move = candidate_moves[0][1:]
        for _, r, c in candidate_moves:
            board[r][c] = AI
            score = evaluate_position(board, r, c, AI)
            board[r][c] = EMPTY
            if score > best_score:
                best_score = score
                best_move = (r, c)
        return best_move

    if difficulty == "hard":
        best_move = candidate_moves[0][1:]
        best_score = -10**9
        for _, r, c in candidate_moves:
            board[r][c] = AI
            score = evaluate_position(board, r, c, AI)
            board[r][c] = EMPTY

            for _, pr, pc in candidate_moves:
                if (pr, pc) == (r, c):
                    continue
                if not is_valid_move(board, pr, pc):
                    continue
                board[pr][pc] = USER
                score -= evaluate_position(board, pr, pc, USER) * 0.7
                board[pr][pc] = EMPTY

            if score > best_score:
                best_score = score
                best_move = (r, c)
        return best_move

    return candidate_moves[0][1:]


def initialize_game():
    st.session_state.board = new_board()
    st.session_state.turn = USER
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.message = "당신의 차례입니다. 돌을 놓아주세요."


st.set_page_config(page_title="오목 게임", page_icon="⚫", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f0e7d3 0%, #e4d7b4 100%);
    }

    div[data-testid="stVerticalBlock"] > div:has(> div > button) {
        gap: 0;
    }

    div.stButton > button {
        width: 2.35rem;
        height: 2.35rem;
        min-width: 2.35rem;
        min-height: 2.35rem;
        padding: 0;
        border-radius: 0;
        border: 1px solid rgba(66, 45, 21, 0.9);
        background: linear-gradient(145deg, #e4c88e 0%, #d2a65d 100%);
        color: #000000;
        font-size: 1.35rem;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
    }

    div.stButton > button:hover {
        background: linear-gradient(145deg, #ebd49f 0%, #d7b067 100%);
    }

    .status-box {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid #d9c8a1;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 14px rgba(83, 63, 28, 0.08);
    }

    .stSidebar {
        background-color: rgba(255, 248, 236, 0.82);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "board" not in st.session_state:
    initialize_game()

if "difficulty" not in st.session_state:
    st.session_state.difficulty = "normal"

st.title("⚫ 오목 게임")
st.caption("컴퓨터와 대결하는 웹 오목게임")

with st.sidebar:
    st.header("게임 설정")
    st.session_state.difficulty = st.selectbox(
        "난이도",
        ["easy", "normal", "hard"],
        index=["easy", "normal", "hard"].index(st.session_state.difficulty),
        format_func=lambda x: {"easy": "쉬움", "normal": "보통", "hard": "어려움"}[x],
    )
    st.button("새 게임", on_click=initialize_game)


if not st.session_state.game_over and st.session_state.turn == AI:
    ai_row, ai_col = choose_ai_move(st.session_state.board, st.session_state.difficulty)
    if ai_row is None or ai_col is None:
        st.session_state.game_over = True
        st.session_state.winner = "무승부"
        st.session_state.message = "판이 가득 차서 무승부입니다."
    else:
        st.session_state.board[ai_row][ai_col] = AI
        if check_win(st.session_state.board, ai_row, ai_col, AI):
            st.session_state.game_over = True
            st.session_state.winner = "컴퓨터"
            st.session_state.message = "컴퓨터가 승리했습니다."
        else:
            st.session_state.turn = USER
            st.session_state.message = "당신의 차례입니다. 돌을 놓아주세요."


st.markdown(
    f"""
    <div class="status-box">
        <strong>상태:</strong> {st.session_state.message}
        <br>
        <strong>난이도:</strong> {st.session_state.difficulty}
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.game_over:
    if st.session_state.winner == "무승부":
        st.warning("무승부입니다. 다시 시작해보세요.")
    else:
        st.success(f"승자: {st.session_state.winner}")

board_points = {(3, 3), (3, 7), (3, 11), (7, 3), (7, 7), (7, 11), (11, 3), (11, 7), (11, 11)}

for r in range(SIZE):
    cols = st.columns(SIZE)
    for c in range(SIZE):
        value = st.session_state.board[r][c]

        if value == EMPTY:
            label = " "
        elif value == USER:
            label = "●"
        else:
            label = "○"

        if (r, c) in board_points and value == EMPTY:
            label = "·"

        disabled = st.session_state.game_over or st.session_state.turn != USER or value != EMPTY

        if cols[c].button(
            label,
            key=f"cell_{r}_{c}",
            use_container_width=True,
            disabled=disabled,
            help=f"{r+1},{c+1}",
        ):
            if not st.session_state.game_over and st.session_state.turn == USER and is_valid_move(st.session_state.board, r, c):
                st.session_state.board[r][c] = USER
                if check_win(st.session_state.board, r, c, USER):
                    st.session_state.game_over = True
                    st.session_state.winner = "사용자"
                    st.session_state.message = "축하합니다! 당신이 승리했습니다."
                else:
                    st.session_state.turn = AI
                    st.session_state.message = "컴퓨터가 수를 생각하고 있습니다..."
                    st.rerun()

                st.rerun()

st.caption("게임 규칙: 같은 색 돌 5개가 연속으로 이어지면 승리합니다.")