import os
import random 
import time
import csv

# Global Variables
gameOver = False
board = []
symbol1 = "●"
symbol2 = "○"
rows = 6
cols = 7

# Performance Metrics
nodesExpanded = 0
maxDepthReached = 0
pruneCount = 0
branchCounts = []

def ClearConsole():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def CreateBoard():
    global board
    for _ in range(rows):
        row = [" "] * cols
        board.append(row)

def PrintBoard():
    ClearConsole()

    for row in board:
        print("|", end=" ")
        for cell in row:
            print(cell, end=" | ")
        print()

    print(" ", end="")
    for i in range(len(board[0])):
        # To show numbers under columns
        print(f" {i+1}  ", end="")  
    print()

def PlaceCounter(pos, symbol):
    global board

    availableRow = None
    for row in range(len(board) - 1, -1, -1):
        if board[row][pos - 1] == " ":
            availableRow = row
            break

    if availableRow is not None:
        board[availableRow][pos - 1] = symbol
        PrintBoard()
        return "Successful"
    else:
        print("Column is full!")
        return "Failed"

def PlayerTurn():
    symbol = symbol1
    selected = False

    while not selected:
        try:
            colPosition = int(input(f"\nSelect a Column (1 - 7): "))
            if 1 <= colPosition <= 7 and PlaceCounter(colPosition, symbol) == "Successful":
                selected = True
            else:
                print("Column must be between 1 and 7")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 7")

def AgentTurn(choice, agentNumber):
    if agentNumber != None:
        symbol = symbol1 if agentNumber == 1 else symbol2
    else:
        symbol = symbol2

    match choice:
        case 1:
            col = RandomAgentMove(board)
        case 2:
            col = RuleBasedAgent(board)
        case 3:
            col = BestMove(board, symbol2, symbol1)

    PlaceCounter(col + 1, symbol)


def GetAvailableCols(board):
    return [col for col in range(cols) if board[0][col] == " "]

def IsFull(board):
    return all(board[0][col] != " " for col in range(cols))

def GetAvailableRow(board, col):
    for row in range(rows - 1, -1, -1):
        if board[row][col] == " ":
            return row
    return None

def ApplyMove(board, col, symbol):
    tempBoard = [row[:] for row in board]
    row = GetAvailableRow(tempBoard, col)
    if row is None:
        return None
    tempBoard[row][col] = symbol
    return tempBoard

def OrderedCols(board):
    center = cols // 2
    return sorted(GetAvailableCols(board), key=lambda col: (abs(col - center), col))

def GetWinningMoves(board, symbol):
    winningMoves = []
    for col in GetAvailableCols(board):
        tempBoard = ApplyMove(board, col, symbol)
        if tempBoard is not None and IsWinningBoard(symbol, tempBoard):
            winningMoves.append(col)
    return winningMoves

def IsWinningBoard(symbol, board):
    # Horizontal
    for r in range(rows):
        count = 0
        for c in range(cols):
            count = count + 1 if board[r][c] == symbol else 0
            if count == 4:
                return True
    # Vertical
    for c in range(cols):
        count = 0
        for r in range(rows):
            count = count + 1 if board[r][c] == symbol else 0
            if count == 4:
                return True
    # Diagonal \
    for r in range(rows - 3):
        for c in range(cols - 3):
            if (board[r][c] == symbol and
                board[r + 1][c + 1] == symbol and
                board[r + 2][c + 2] == symbol and
                board[r + 3][c + 3] == symbol):
                return True
    # Diagonal /
    for r in range(3, rows):
        for c in range(cols - 3):
            if (board[r][c] == symbol and
                board[r - 1][c + 1] == symbol and
                board[r - 2][c + 2] == symbol and
                board[r - 3][c + 3] == symbol):
                return True
    return False

def GetWinPattern(symbol, board):
    # Horizontal
    for r in range(rows):
        count = 0
        for c in range(cols):
            count = count + 1 if board[r][c] == symbol else 0
            if count == 4:
                return "horizontal"
            
    # Vertical
    for c in range(cols):
        count = 0
        for r in range(rows):
            count = count + 1 if board[r][c] == symbol else 0
            if count == 4:
                return "vertical"
            
    # Diagonal \
    for r in range(rows - 3):
        for c in range(cols - 3):
            if (board[r][c] == symbol and
                board[r + 1][c + 1] == symbol and
                board[r + 2][c + 2] == symbol and
                board[r + 3][c + 3] == symbol):
                return "diagonal_\\"
            
    # Diagonal /
    for r in range(3, rows):
        for c in range(cols - 3):
            if (board[r][c] == symbol and
                board[r - 1][c + 1] == symbol and
                board[r - 2][c + 2] == symbol and
                board[r - 3][c + 3] == symbol):
                return "diagonal_/"
    return False

def PrintWin(symbol, board, isAgentGame):
    if isAgentGame == True:
        playerName = "Agent 1" if symbol == symbol1 else "Agent 2"
    else:
        playerName = "Player" if symbol == symbol1 else "Agent"

    if IsWinningBoard(symbol, board):
        print(f"{playerName} wins")
        return True

    if IsFull(board):
        print("It's a draw!")
        return True

    return False

def RandomAgentMove(board):
    # Picks out of a random column that is available
    return random.choice(GetAvailableCols(board))

def RuleBasedAgent(board):
    # Creates a temporary board to check whether a move from either itself or the opponent will win
    # Based on this will decide on trying to win or to block the opponent from winning

    # Try to win
    for col in OrderedCols(board):
        tempBoard = ApplyMove(board, col, symbol2)
        if IsWinningBoard(symbol2, tempBoard):
            return col

    # Try to block
    for col in OrderedCols(board):
        tempBoard = ApplyMove(board, col, symbol1)
        if IsWinningBoard(symbol1, tempBoard):
            return col

    # Else
    return random.choice(OrderedCols(board))

def EvaluateWindow(window, agentSymbol, playerSymbol):
        # Goes through the captured 'window' seeing how many of each symbol it contains

        scoreWeights = {
            4: 100000, # four in a row (should be caught by terminal check first)
            3: 1200,   # three of ours + one empty
            2: 80,     # two of ours + two empty
            1: 2       # one of ours + three empty
            }
        
        agentCount = window.count(agentSymbol)
        playerCount = window.count(playerSymbol)
        emptyCount = window.count(" ")
        
        if agentCount and playerCount:
            return 0
        if agentCount:
            if agentCount == 3 and emptyCount == 1:
                return 1200
            if agentCount == 2 and emptyCount == 2:
                return 80
            return scoreWeights.get(agentCount, 0)
        if playerCount:
            if playerCount == 3 and emptyCount == 1:
                return -1500
            if playerCount == 2 and emptyCount == 2:
                return -90
            return -scoreWeights.get(playerCount, 0)
        return 0

def HeuristicScore(board, agentSymbol, playerSymbol):
    score = 0
    centerCol = cols // 2
    centerCount = sum(1 for r in range(rows) if board[r][centerCol] == agentSymbol)
    enemyCenterCount = sum(1 for r in range(rows) if board[r][centerCol] == playerSymbol)
    score += centerCount * 18
    score -= enemyCenterCount * 18

    # Horizontal runs
    for r in range(rows):
        for c in range(cols - 3):
            window = [board[r][c + i] for i in range(4)]
            score += EvaluateWindow(window, agentSymbol, playerSymbol)

    # Vertical runs
    for c in range(cols):
        for r in range(rows - 3):
            window = [board[r + i][c] for i in range(4)]
            score += EvaluateWindow(window, agentSymbol, playerSymbol)

    # Diagonal \ runs
    for r in range(rows - 3):
        for c in range(cols - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += EvaluateWindow(window, agentSymbol, playerSymbol)

    # Diagonal / runs
    for r in range(3, rows):
        for c in range(cols - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += EvaluateWindow(window, agentSymbol, playerSymbol)

    score += len(GetWinningMoves(board, agentSymbol)) * 2500
    score -= len(GetWinningMoves(board, playerSymbol)) * 3000

    return score

def MiniMax(board, depth, alpha, beta, isMaximising, agentSymbol, playerSymbol, maxDepth=3):
    global nodesExpanded, maxDepthReached, pruneCount, branchCounts

    # Metric Variables
    nodesExpanded += 1
    maxDepthReached = max(maxDepthReached, depth)

    legalMoves = GetAvailableCols(board)
    branchCounts.append(len(legalMoves))

    if IsWinningBoard(agentSymbol, board):
        return 100000 - depth
    elif IsWinningBoard(playerSymbol, board):
        return depth - 100000
    elif IsFull(board):
        return 0
    if depth >= maxDepth:
        # Don't go any further 
        return HeuristicScore(board, agentSymbol, playerSymbol)
    
    if isMaximising:
        maxEval = float("-inf")

        for col in OrderedCols(board):
            tempBoard = ApplyMove(board, col, agentSymbol)
            evalScore = MiniMax(tempBoard, depth + 1, alpha, beta, False, agentSymbol, playerSymbol, maxDepth)
            # ^ recursive call to minimax whilst changing to minimizing - simulating opponent's move
            maxEval = max(maxEval, evalScore)
            alpha = max(alpha, evalScore)
            if beta <= alpha:
                # prunes branch as minimising player is likely avoid this path
                pruneCount +=1
                break

        return maxEval
    
    else:
        minEval = float("inf")

        for col in OrderedCols(board):
            tempBoard = ApplyMove(board, col, playerSymbol)
            evalScore = MiniMax(tempBoard, depth + 1, alpha, beta, True, agentSymbol, playerSymbol, maxDepth)
            minEval = min(minEval, evalScore)
            beta = min(beta, evalScore)
            if beta <= alpha:
                pruneCount +=1
                break

        return minEval
    
def BestMove(board, agentSymbol, playerSymbol, maxDepth=5):
    # Prioritise direct wins and emergency blocks before deeper search.
    winningMoves = GetWinningMoves(board, agentSymbol)
    if winningMoves:
        return winningMoves[0]

    blockingMoves = GetWinningMoves(board, playerSymbol)
    if blockingMoves:
        return blockingMoves[0]

    bestValue = float("-inf")
    bestCol = None
    safeMoves = []
    riskyMoves = []

    for col in OrderedCols(board):
        tempBoard = ApplyMove(board, col, agentSymbol)
        opponentWinningReplies = GetWinningMoves(tempBoard, playerSymbol)
        if opponentWinningReplies:
            riskyMoves.append(col)
        else:
            safeMoves.append(col)

    candidateMoves = safeMoves if safeMoves else OrderedCols(board)

    # For every column, simulate placement and score it with minimax.
    for col in candidateMoves:
        tempBoard = ApplyMove(board, col, agentSymbol)
        moveValue = MiniMax(tempBoard, 0, float("-inf"), float("inf"), False, agentSymbol, playerSymbol, maxDepth)
        moveValue += (cols // 2) - abs(col - (cols // 2))
        # ^ maximising set to false because counter placement already counts as a maximising effort
        if moveValue > bestValue:
            bestValue = moveValue
            bestCol = col

    if bestCol is None and riskyMoves:
        return riskyMoves[0]
    return bestCol

def PlayerVsAgent():
    ClearConsole()
    print("Who would you like to play?")
    print("1) Random Agent\n2) Rule-based Agent\n3) Minimax Agent\n")

    choice = int(input("Please choose an option (1-3): "))
    PrintBoard()

    while True:
        PlayerTurn()
        if PrintWin(symbol1, board, False):
            break
        AgentTurn(choice, None)
        if PrintWin(symbol2, board, False):
            break

def AgentVsAgent():
    ClearConsole()

    print("Agent VS Agent!\n")
    print("1) Random Agent\n2) Rule-based Agent\n3) Minimax Agent\n")
    firstAgent = int(input("\n1st Choice - Please choose an option (1-3): "))
    secondAgent = int(input("\n2nd Choice - Please choose an option (1-3): "))

    PrintBoard()

    while True:
        AgentTurn(firstAgent, 1)
        time.sleep(0.5)
        if PrintWin(symbol1, board, True):
            break
        AgentTurn(secondAgent, 2)
        time.sleep(0.5)
        if PrintWin(symbol2, board, True):
            break

def AutomatedAgentVsAgent(agentA, agentB):
    while True:
        AgentTurn(agentA, 1)
        if PrintWin(symbol1, board, True):
            return "A"

        AgentTurn(agentB, 2)
        if PrintWin(symbol2, board, True):
            return "B"

        if IsFull(board):
            print("It's a draw!")
            return "D"


""" PERFORMANCE METRICS """

def Evaluation(firstAgentChoice, secondAgentChoice, numGames=500, outputFile="RuleBasedVsMinimax3.csv"):
    fieldNames = [
        "GameIndex",
        "Winner",
        "WinPattern",
        "TotalMoves",
        "GameDuration",
        "NodesExpanded",
        "AverageBranching",
        "MaxDepthReached",
        "PruneCount",
        "MoveTimeAvgMs"
    ]

    with open(outputFile, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldNames)
        writer.writeheader()

        for gameIndex in range(1, numGames + 1):
            global board, nodesExpanded, maxDepthReached, pruneCount
            gameStart = time.perf_counter() # Timer starts for each game
            board = []
            CreateBoard()

            # Reset metrics
            nodesExpanded = 0
            maxDepthReached = 0
            pruneCount = 0
            gameDuration = 0
    
            totalMoves = 0
            totalMoveTime = 0.0
            winner = None
            winPattern = "N/A"
            print("Game: ", gameIndex)
            while True:
                # Agent 1
                start = time.perf_counter() # Timer starts for each move
                AgentTurn(firstAgentChoice, agentNumber=1)
                duration = (time.perf_counter() - start) * 1000 # Time for move logged
                totalMoveTime += duration
                totalMoves += 1
                if IsWinningBoard(symbol1, board):
                    winner = "Agent1"
                    winPattern = GetWinPattern(symbol1, board)
                    break
                if IsFull(board):
                    winner = "Draw"
                    break

                # Agent 2
                start = time.perf_counter()
                AgentTurn(secondAgentChoice, agentNumber=2)
                duration = (time.perf_counter() - start) * 1000
                totalMoveTime += duration
                totalMoves += 1
                if IsWinningBoard(symbol2, board):
                    winner = "Agent2"
                    winPattern = GetWinPattern(symbol2, board)
                    break
                if IsFull(board):
                    winner = "Draw"
                    break

            gameEnd = time.perf_counter() # Game end logged and duration calculated
            gameDuration = gameEnd - gameStart

            # Write this game’s metrics
            writer.writerow({
                "GameIndex": gameIndex,
                "Winner": winner,
                "WinPattern": winPattern,
                "TotalMoves": totalMoves,
                "GameDuration": gameDuration,
                "NodesExpanded": nodesExpanded,
                #"AverageBranching": f"{(sum(branchCounts) / len(branchCounts)):.2f}", 
                # Mean branches i.e sum / cardinality
                "MaxDepthReached": maxDepthReached,
                "PruneCount": pruneCount,
                "MoveTimeAvgMs": f"{(totalMoveTime/totalMoves):.3f}"
            })
            
    print(f"Batch evaluation complete! Results in {outputFile}")


def MainMenu():
    print("\nWelcome to Connect 4!\n")
    print("Please pick:\n1) Player VS Agent\n2) Agent VS Agent")

    choice = int(input("\nPlease choose an option (1-2): "))

    match choice:
        case 1:
            PlayerVsAgent()
        case 2:
            AgentVsAgent()

if __name__ == "__main__":
    # 1: Random Agent, 2: Rule Based, 3: Minimax
    #Evaluation(1,2,500) # 3rd param is noOfGames
    CreateBoard()
    MainMenu()

    
