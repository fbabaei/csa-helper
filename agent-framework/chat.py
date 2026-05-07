"""Interactive REPL against the orchestrator team."""
from __future__ import annotations

from dotenv import load_dotenv

from build_team import build_team


def main() -> None:
    load_dotenv()
    team = build_team()
    print(f"CSA Helper ready. {len(team.specialists)} specialists registered.")
    print("Type 'exit' to quit, ':trace' to toggle handoff trace.\n")
    show_trace = True
    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            break
        if prompt == ":trace":
            show_trace = not show_trace
            print(f"(trace {'on' if show_trace else 'off'})")
            continue
        answer, trace = team.ask(prompt)
        if show_trace and trace:
            for hop in trace:
                print(f"  -> handoff to {hop['agent']}")
        print(f"\nbot> {answer}\n")


if __name__ == "__main__":
    main()
