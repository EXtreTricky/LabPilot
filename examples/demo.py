import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.my_tool.core.rules import recommend,risk_hint
rooms=[{'id':1,'name':'计算机实验室','capacity':36,'tags':'Python,编程','status':'available'}]
print(recommend(rooms,'Python',20));print(risk_hint('设备有异味'))
