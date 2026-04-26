class SolutionMemoryIndex:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add_solution(self, goal: str, solution: dict) -> dict:
        item = {"goal": goal, "solution": solution, "status": "indexed"}
        self.items.append(item)
        return item

    def search(self, goal: str) -> list[dict]:
        return [i for i in self.items if any(token in i["goal"] for token in goal.split())]
