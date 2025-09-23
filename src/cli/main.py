from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("src.protocol.http.app:create_app", factory=True, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
