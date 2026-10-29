"""AX8 PPTX - standalone launcher.

Runs the pipeline without needing the package to be installed: the parent
directory is added to sys.path so `import ax8pptx` resolves from here.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ax8pptx.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
