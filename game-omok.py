import json
import random
from pathlib import Path

import pandas as pd
import streamlit as st

SIZE = 15
EMPTY = 0
USER = 1
AI = 2
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
USER_DB_PATH = Path(__file__).with_name("omok_users.json")


def get_default_difficulty_stats():
    return {
        "easy": {"wins": 0, "losses": 0, "draws": 0},
        "normal": {"wins": 0, "losses": 0, "draws": 0},
        "hard": {"wins": 0, "losses": 0, "draws": 0},
    }


def normalize_user(user):
    difficulty_stats = user.get("difficulty_stats")
    if not isinstance(difficulty_stats, dict):
        difficulty_stats = get_default_difficulty_stats()

    for level in ["easy", "normal", "hard"]:
        level_stats = difficulty_stats.get(level, {})
        if not isinstance(level_stats, dict):
            level_stats = {}
        difficulty_stats[level] = {
            "wins": int(level_stats.get("wins", 0) or 0),
            "losses": int(level_stats.get("losses", 0) or 0),
            "draws": int(level_stats.get("draws", 0) or 0),
        }

    return {
        "name": str(user.get("name", "게스트")).strip(),
        "wins": int(user.get("wins", 0) or 0),
        "losses": int(user.get("losses", 0) or 0),
        "draws": int(user.get("draws", 0) or 0),
        "difficulty_stats": difficulty_stats,
    }


def load_users():
    if not USER_DB_PATH.exists():
        default_users = [{"name": "게스트", "wins": 0, "losses": 0, "draws": 0, "difficulty_stats": get_default_difficulty_stats()}]
        USER_DB_PATH.write_text(json.dumps(default_users, ensure_ascii=False, indent=2), encoding="utf-8")
        return default_users

    try:
        data = json.loads(USER_DB_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            normalized = []
            for user in data:
                if not isinstance(user, dict):
                    continue
                normalized.append(normalize_user(user))
            return normalized
    except Exception:
        pass

    fallback = [{"name": "게스트", "wins": 0, "losses": 0, "draws": 0, "difficulty_stats": get_default_difficulty_stats()}]
    USER_DB_PATH.write_text(json.dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
    return fallback


def save_users(users):
    USER_DB_PATH.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def get_user_record(name):
    users = st.session_state.users
    for user in users:
        if user["name"] == name:
            return user
    return {
        "name": name, 
        "wins": 0, 
        "losses": 0, 
        "draws": 0,
        "difficulty_stats": get_default_difficulty_stats(),
    }


def ensure_user_exists(name):
    clean_name = str(name).strip()
    if not clean_name:
        return None
    for user in st.session_state.users:
        if user["name"] == clean_name:
            return user
    user = {"name": clean_name, "wins": 0, "losses": 0, "draws": 0, "difficulty_stats": get_default_difficulty_stats()}
    st.session_state.users.append(user)
    save_users(st.session_state.users)
    return user


def update_user_stats(name, result, difficulty="normal"):
    user = ensure_user_exists(name)
    if user is None:
        return

    if result == "win":
        user["wins"] += 1
    elif result == "loss":
        user["losses"] += 1
    elif result == "draw":
        user["draws"] += 1

    if "difficulty_stats" not in user or not isinstance(user["difficulty_stats"], dict):
        user["difficulty_stats"] = get_default_difficulty_stats()

    if difficulty not in user["difficulty_stats"]:
        user["difficulty_stats"][difficulty] = {"wins": 0, "losses": 0, "draws": 0}

    if result == "win":
        user["difficulty_stats"][difficulty]["wins"] += 1
    elif result == "loss":
        user["difficulty_stats"][difficulty]["losses"] += 1
    elif result == "draw":
        user["difficulty_stats"][difficulty]["draws"] += 1

    save_users(st.session_state.users)


def get_user_win_rate(user):
    total = user["wins"] + user["losses"] + user["draws"]
    if total == 0:
        return 0.0
    return (user["wins"] / total) * 100


def get_difficulty_win_rate(stats):
    total = stats["wins"] + stats["losses"] + stats["draws"]
    if total == 0:
        return 0.0
    return (stats["wins"] / total) * 100


def record_game_result(winner):
    if st.session_state.get("game_result_recorded", False):
        return

    st.session_state.game_result_recorded = True
    current_user = st.session_state.get("selected_user")
    if current_user is None:
        return

    difficulty = st.session_state.get("difficulty", "normal")

    if winner == "사용자":
        update_user_stats(current_user, "win", difficulty)
    elif winner == "컴퓨터":
        update_user_stats(current_user, "loss", difficulty)
    else:
        update_user_stats(current_user, "draw", difficulty)


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
    st.session_state.game_result_recorded = False
    st.session_state.result_notice_shown = False


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
        background: linear-gradient(145deg, #f1d7a1 0%, #d7b067 100%);
        border-color: rgba(42, 30, 14, 1);
    }

    .status-box {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid #d9c8a1;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 14px rgba(83, 63, 28, 0.08);
    }

    .turn-chip {
        display: inline-block;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        font-weight: 700;
        margin-top: 0.3rem;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);
    }

    .turn-black {
        background: #111111;
        color: white;
    }

    .turn-white {
        background: #f4f4f4;
        color: #121212;
        border: 1px solid rgba(0,0,0,0.2);
    }

    .stSidebar {
        background-color: rgba(255, 248, 236, 0.82);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "selected_user" not in st.session_state:
    st.session_state.selected_user = st.session_state.users[0]["name"] if st.session_state.users else "게스트"

if "board" not in st.session_state:
    initialize_game()

if "difficulty" not in st.session_state:
    st.session_state.difficulty = "normal"

if "game_mode" not in st.session_state:
    st.session_state.game_mode = "computer"

st.title("⚫ 오목 게임")
st.caption("컴퓨터와 대결하는 웹 오목게임")

with st.sidebar:
    st.header("게임 설정")

    st.session_state.game_mode = st.selectbox(
        "게임 모드",
        ["computer", "human"],
        index=0 if st.session_state.game_mode == "computer" else 1,
        format_func=lambda x: {"computer": "컴퓨터 대전", "human": "사람 대 사람"}[x],
    )

    user_names = [user["name"] for user in st.session_state.users]
    selected_index = user_names.index(st.session_state.selected_user) if st.session_state.selected_user in user_names else 0
    st.session_state.selected_user = st.selectbox("사용자 선택", user_names, index=selected_index)

    new_name = st.text_input("새 사용자 추가", value="")
    if st.button("사용자 추가"):
        cleaned = new_name.strip()
        if cleaned:
            if cleaned not in user_names:
                st.session_state.users.append({
                    "name": cleaned,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "difficulty_stats": get_default_difficulty_stats(),
                })
                save_users(st.session_state.users)
                st.session_state.selected_user = cleaned
                st.rerun()
            else:
                st.warning("이미 존재하는 사용자입니다.")
        else:
            st.warning("사용자 이름을 입력해주세요.")

    st.session_state.difficulty = st.selectbox(
        "난이도",
        ["easy", "normal", "hard"],
        index=["easy", "normal", "hard"].index(st.session_state.difficulty),
        format_func=lambda x: {"easy": "쉬움", "normal": "보통", "hard": "어려움"}[x],
    )
    st.button("새 게임", on_click=initialize_game)

    current_user = get_user_record(st.session_state.selected_user)
    total_games = current_user["wins"] + current_user["losses"] + current_user["draws"]
    win_rate = get_user_win_rate(current_user)
    st.markdown("---")
    st.subheader("전적")
    st.write(f"사용자: {st.session_state.selected_user}")
    st.write(f"승: {current_user['wins']} | 패: {current_user['losses']} | 무: {current_user['draws']}")
    st.write(f"승률: {win_rate:.1f}% ({total_games}게임)")

    difficulty_labels = {"easy": "쉬움", "normal": "보통", "hard": "어려움"}
    chart_rows = []
    for level in ["easy", "normal", "hard"]:
        stats = current_user.get("difficulty_stats", {}).get(level, {"wins": 0, "losses": 0, "draws": 0})
        chart_rows.append({
            "난이도": difficulty_labels[level],
            "승": stats.get("wins", 0),
            "패": stats.get("losses", 0),
            "무": stats.get("draws", 0),
        })

    chart_df = pd.DataFrame(chart_rows)
    st.subheader("난이도별 통계")
    st.bar_chart(chart_df.set_index("난이도"), use_container_width=True)

    st.subheader("난이도별 상세")
    for level in ["easy", "normal", "hard"]:
        stats = current_user.get("difficulty_stats", {}).get(level, {"wins": 0, "losses": 0, "draws": 0})
        rate = get_difficulty_win_rate(stats)
        st.write(f"- {difficulty_labels[level]}: {stats['wins']}승 / {stats['losses']}패 / {stats['draws']}무 / 승률 {rate:.1f}%")

    leaderboard = sorted(st.session_state.users, key=lambda u: (get_user_win_rate(u), u["wins"], u["draws"]), reverse=True)
    st.subheader("랭킹")
    for idx, user in enumerate(leaderboard[:5], start=1):
        rate = get_user_win_rate(user)
        st.write(f"{idx}. {user['name']} - {rate:.1f}% ({user['wins']}승)")


if not st.session_state.game_over and st.session_state.game_mode == "computer" and st.session_state.turn == AI:
    ai_row, ai_col = choose_ai_move(st.session_state.board, st.session_state.difficulty)
    if ai_row is None or ai_col is None:
        st.session_state.game_over = True
        st.session_state.winner = "무승부"
        st.session_state.message = "판이 가득 차서 무승부입니다."
        record_game_result("무승부")
    else:
        st.session_state.board[ai_row][ai_col] = AI
        if check_win(st.session_state.board, ai_row, ai_col, AI):
            st.session_state.game_over = True
            st.session_state.winner = "컴퓨터"
            st.session_state.message = "컴퓨터가 승리했습니다."
            record_game_result("컴퓨터")
        else:
            st.session_state.turn = USER
            st.session_state.message = "당신의 차례입니다. 돌을 놓아주세요."


if st.session_state.game_mode == "computer":
    turn_class = "turn-black" if st.session_state.turn == USER else "turn-white"
    turn_label = "흑돌 차례" if st.session_state.turn == USER else "백돌 차례"
else:
    turn_class = "turn-black" if st.session_state.turn == USER else "turn-white"
    turn_label = "플레이어 1 차례" if st.session_state.turn == USER else "플레이어 2 차례"

st.markdown(
    f"""
    <div class="status-box">
        <strong>상태:</strong> {st.session_state.message}
        <br>
        <strong>난이도:</strong> {st.session_state.difficulty}
        <br>
        <span class="turn-chip {turn_class}">{turn_label}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.game_over:
    if st.session_state.winner == "무승부":
        st.warning("무승부입니다. 다시 시작해보세요.")
    else:
        st.success(f"승자: {st.session_state.winner}")

    if not st.session_state.get("result_notice_shown", False):
        st.session_state.result_notice_shown = True

board_points = {(3, 3), (3, 7), (3, 11), (7, 3), (7, 7), (7, 11), (11, 3), (11, 7), (11, 11)}

board_container = st.container()
with board_container:
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

            if st.session_state.game_mode == "computer":
                clickable = not st.session_state.game_over and st.session_state.turn == USER and value == EMPTY
            else:
                clickable = not st.session_state.game_over and value == EMPTY

            disabled = not clickable

            if cols[c].button(
                label,
                key=f"cell_{r}_{c}",
                use_container_width=True,
                disabled=disabled,
                help=f"{r+1},{c+1}",
            ):
                if not st.session_state.game_over and is_valid_move(st.session_state.board, r, c):
                    current_player = st.session_state.turn
                    st.session_state.board[r][c] = current_player

                    if check_win(st.session_state.board, r, c, current_player):
                        st.session_state.game_over = True
                        if st.session_state.game_mode == "computer":
                            st.session_state.winner = "사용자" if current_player == USER else "컴퓨터"
                            st.session_state.message = "축하합니다! 당신이 승리했습니다." if current_player == USER else "컴퓨터가 승리했습니다."
                            record_game_result(st.session_state.winner)
                        else:
                            st.session_state.winner = "플레이어 1" if current_player == USER else "플레이어 2"
                            st.session_state.message = f"{st.session_state.winner}가 승리했습니다!"
                    else:
                        if st.session_state.game_mode == "computer":
                            if current_player == USER:
                                st.session_state.turn = AI
                                st.session_state.message = "컴퓨터가 수를 생각하고 있습니다..."
                            else:
                                st.session_state.turn = USER
                                st.session_state.message = "당신의 차례입니다. 돌을 놓아주세요."
                        else:
                            st.session_state.turn = AI if current_player == USER else USER
                            st.session_state.message = "플레이어 1 차례입니다." if st.session_state.turn == USER else "플레이어 2 차례입니다."

                    st.rerun()

st.caption("게임 규칙: 같은 색 돌 5개가 연속으로 이어지면 승리합니다.")