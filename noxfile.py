"""This file allows us to run tests on multiple python versions using 'nox'."""

import nox


@nox.session(python=["3.11", "3.12", "3.13", "3.14"])  # type: ignore[misc]
def test(session: nox.Session) -> None:
    session.run("uv", "sync", external=True)
    session.run("uv", "run", "pytest", "-x", "--log-cli-level=ERROR", external=True)
