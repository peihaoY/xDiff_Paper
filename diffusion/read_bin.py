import numpy as np
# 从 bin 文件读取数据
with open('../rlflexric/dudata/ctrl.bin', "rb") as f:
    loaded_action = np.fromfile(f, dtype=np.float32)

print("读取的数据：", loaded_action)