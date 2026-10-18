# Members

Every member adds a folder named after their GitHub username, and commits it
themselves. The folder contains three files:

| File | How you make it |
|---|---|
| `machine.txt` | `bash tools/machine_info.sh USERNAME "laptop model, operating system"` |
| `measurements.md` | The measurements you took on your own laptop in class, with the commands you used |
| `sweep.csv` | `bash tools/sweep.sh USERNAME` |

`python3 tools/check.py` lists the folders that are still incomplete, and who
committed each one.
