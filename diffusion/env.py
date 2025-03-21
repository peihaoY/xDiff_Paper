import sqlite3
import numpy as np
import gym
from gym import spaces
import struct
import os
import copy
import csv
from collections import defaultdict

class icic_env(gym.Env):
    def __int__(self):
        #self.action_space = spaces.Discrete(2)  # 两个连续动作 Box
        self.observation_space = spaces.Box(low=0, high=1, shape=(17,), dtype=np.float32)  # 17个浮点数的向量
        
        self.state = []
        self.MAC = []
        self.KPM = []

    def initlize(self, user_num, action_dim):
        self.last_macstate = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.last_kpmstate = [[0] * 8 for _ in range(user_num)]
        self.action_space = spaces.Box(low=-1, high=1, shape=(action_dim,), dtype=np.float32)   #(-1,1) 浮点数的向量
        self.user_num = user_num
        self.action_dim = action_dim
    
    def reset(self):
        self.state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        return self.state

    def init_file(self):    
        #with open('../rlflexric/dudata/ctrl.bin', 'rb+') as file:
        #    numbers = (40, 30, 30, 1)
        #   file.write(struct.pack('iiii', *numbers))
        matrix = [[0]*10 for _ in range(self.user_num)]
        file_path = "../rlflexric/dudata/ctrl.csv"
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(matrix)
            
    def get_ue_id(self):
        # 初始化存储gnb和UE信息的字典
        gnb_data = defaultdict(set)
        
        # 读取文件
        file_path = "../rlflexric/dudata/KPM_UE.txt"

        while 1:
            with open(file_path, 'r') as file:
                lines = file.readlines()[-10:]  # 获取文件的最后两行
            
            if len(lines[-1].split()) < 8:
                continue

            for line in lines:
                parts = line.strip().split()
                gnb_id = int(parts[2])  # 第三列为gnb标号
                ue_id = int(parts[0])   # 第一列为UE的ID
                gnb_data[gnb_id].add(ue_id)  # 将UE ID添加到对应的gnb集合中
            
            return gnb_data

        # with open(file_path, "r") as file:
        #     for line in file:
        #         parts = line.strip().split()
        #         gnb_id = int(parts[2])  # 第三列为gnb标号
        #         ue_id = int(parts[0])   # 第一列为UE的ID
        #         gnb_data[gnb_id].add(ue_id)  # 将UE ID添加到对应的gnb集合中
        # return gnb_data
                
    def get_UEmac_layer_info(self, ue_id, gnb_id ):
        self.mac_state = []
        # 连接到数据库
        conn = sqlite3.connect('../rlflexric/dudata/xapp_db_')
        cursor = conn.cursor()
        # 8 numbers for each UE
        # YPH would like to add more data here in the future
        # I add 10 numbers of the UE
        #print("get_UEmac_layer_info############ue_id", ue_id, "gnb_id", gnb_id)
        query = f"""
        SELECT dl_curr_tbs, dl_sched_rb, pusch_snr, pucch_snr, wb_cqi, dl_mcs1, ul_mcs1, phr, dl_bler, ul_bler
        FROM MAC_UE 
        WHERE nb_id = ? AND rnti = ? 
        ORDER BY tstamp DESC 
        LIMIT 1;
        """
        cursor.execute(query, (gnb_id, ue_id,))
        #cursor.execute("SELECT dl_sched_rb,ul_sched_rb,pusch_snr,pucch_snr,wb_cqi,phr,dl_bler,ul_bler FROM MAC_UE WHERE rnti = 1 ORDER BY tstamp DESC LIMIT 1;")
        self.mac_state = cursor.fetchall()
        if len(self.mac_state[0]) < 8:
            self.mac_state[0] = self.last_macstate
        else:
            self.last_macstate = self.mac_state[0]      
        
        # Check the total number of records
        
        '''
        count_query = "SELECT COUNT(*) FROM MAC_UE;"
        cursor.execute(count_query)
        record_count = cursor.fetchone()[0]

        # If the number of records exceeds 100, delete the oldest 50 records
        if record_count > 100:
            delete_query = """
            DELETE FROM MAC_UE 
            WHERE tstamp IN (
            SELECT tstamp 
            FROM MAC_UE 
            ORDER BY tstamp ASC 
            LIMIT 50
            );
            """
            cursor.execute(delete_query)
            conn.commit()    
        '''
        # 实际运行的时候读取之后清空 it does not work
        # cursor.execute("SELECT MAX(tstamp) FROM MAC_UE")
        # latest_id = cursor.fetchone()[0]
        # cursor.execute('DELETE FROM MAC_UE WHERE tstamp != ?', (latest_id,))
        conn.close()

    def get_UEkpm_info(self, ue_id, gnb_id, user_num):
        '''ue_id, DRB_pdcpSduVolumeDL, DRB_pdcpSduVolumeUL（这里换成了gnb_id）, DRB_RlcSduDelayDL, DRB_UEThpDL, DRB_UEThpUL, RRU_PrbTotDL, RRU_PrbTotUL '''
        data_ueid = []

        # with open('../rlflexric/dudata/KPM_UE.txt', 'r') as file:
        #         lines = file.readlines()[-user_num:]  # 获取文件的最后两行
        # for line in lines:
        #      data = [float(x) for x in line.split()]
        #      if int(data[2]) == gnb_id and int(data[0]) == ue_id:
        #         data_ueid = data
                
        # self.kpm_state = data_ueid
        aa = 0
        while 1:
            with open('../rlflexric/dudata/KPM_UE.txt', 'r') as file:
                lines = file.readlines()[-user_num:]  # 获取文件的最后两行
            
            if len(lines[-1].split()) < 8:
                continue

            for line in lines:
                data = [float(x) for x in line.split()]
                if int(data[2]) == gnb_id and int(data[0]) == ue_id:
                   data_ueid = data

            if len(data_ueid) < 8:
                continue
            else:
            #     if data_ueid == self.last_kpmstate[ue_id-1] and data_ueid[4] != 0:
            #         continue
            #     else:
            #         self.last_kpmstate[ue_id-1] = copy.deepcopy(data_ueid)
                self.kpm_state = data_ueid
                break
            

    def get_state(self, ue_id, gnb_id, user_num):   #在这里处理数据
        
        self.get_UEmac_layer_info(ue_id, gnb_id,)
        self.get_UEkpm_info(ue_id, gnb_id, user_num)
        # print("#asdnjkfajdnfkeanvedlnvd")
        self.state = list(self.mac_state[0]) + self.kpm_state  #问题是，每一个的最大最小值都不同

        self.MAC = list(self.mac_state[0])
        #dl_curr_tbs, dl_sched_rb, pusch_snr, pucch_snr, wb_cqi, dl_mcs1, ul_mcs1, phr, dl_bler, ul_bler
        self.MAC[0] = (self.MAC[0]-0)/3000          
        self.MAC[1] = (self.MAC[1]-0)/106                        
        # pusch_snr,pucch_snr, 0-70
        self.MAC[2] = (self.MAC[2]-0)/70           
        self.MAC[3] = (self.MAC[3]-0)/50
        # wb_cqi 0-15
        self.MAC[4] = (self.MAC[4]-0)/15
        # dl_mcs1, ul_mcs1
        self.MAC[5] = self.MAC[5]/28           
        self.MAC[6] = self.MAC[6]/28
        # phr -24-70
        self.MAC[7] = (self.MAC[7]-20)/(70-20)
        # dl_bler,ul_bler 0-0.5
        self.MAC[8] = self.MAC[8]/0.5           
        self.MAC[9] = self.MAC[9]/0.5

        self.KPM = self.kpm_state
        # 这里的数据针对的是100ms的kpm
        # DRB_pdcpSduVolumeDL, DRB_pdcpSduVolumeUL   0-80000
        self.KPM[1] = self.KPM[1]/20000
        # self.KPM[2] = self.KPM[3]/20000
        #DRB_RlcSduDelayDL, 0-1000    #there will be a peak when states is changing 
        '''
        if self.KPM[3] > 1000:
            self.KPM[3] = 1000
        else:
            self.KPM[3] = self.KPM[3]/1000
        '''
        self.KPM[3] = self.KPM[3]/1000
        #DRB_UEThpDL, DRB_UEThpUL, kbps
        self.KPM[4] = self.KPM[4]/1000   #倒数第四个值是downlink
        self.KPM[5] = self.KPM[5]/1000
        #RRU_PrbTotUL, RRU_PrbTotUL  0-70000
        self.KPM[6] = self.KPM[6]/1000
        self.KPM[7] = self.KPM[7]/1000

        return self.state, self.MAC, self.KPM

    def get_all_state(self, gnb_id_array, user_num):
        self.UE_MAC = []
        self.UE_KPM = []
        self.RRU_ThpDL_UE = []
        self.DRB_Delay = []
        self.BLER = []
        self.RRU_PrbTotDL = []
        max_uenum = 3
        
        gnb_data = self.get_ue_id()
        
        #for gnb_id in gnb_id_array:
          #for ue_id in range(1, max_uenum):
        for gnb_id, ue_ids in gnb_data.items():
          for ue_id in ue_ids:
            UE_state, ue_mac_i, ue_kpm_i = self.get_state(ue_id, gnb_id, user_num)
  
            self.UE_MAC.append(ue_mac_i)
            self.BLER.append(ue_mac_i[8])
            self.UE_KPM.append(ue_kpm_i)
  
            self.DRB_Delay.append(ue_kpm_i[3])
            self.RRU_ThpDL_UE.append(ue_kpm_i[4])
            self.RRU_PrbTotDL.append(ue_kpm_i[6])
        return self.UE_MAC

    def send_action(self, action, a, ue_num, gnb_num, user_split): #action is a map
        #while True:
        #with open('../rlflexric/dudata/ctrl.bin', 'wb+') as file:
        #    action.tofile(file)
        #为了方便查看，这里改成采用csv文件存储

        file_path = "../rlflexric/dudata/ctrl.csv"
        #file_exists = os.path.isfile(file_path)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow([a, ue_num, gnb_num] + user_split) #

            for i in range(0, len(action), 10):
                writer.writerow(action[i:i+10])
        #print("数据已写入 ctrl.csv 文件。")

    def reset(self):
        self.state = np.random.rand(20)
        return np.array(self.state)

    def caculate_reward(self, action, user_num):  
        avg_throughput = 0
        avg_delay = 0
        avg_prbs = 0
        demand = 200
        latency_requirment = 1000000
        for i in range(0, user_num):
            avg_throughput = avg_throughput + self.RRU_ThpDL_UE[i]
            avg_delay = avg_delay + self.DRB_Delay[i]
            avg_prbs = avg_prbs + self.RRU_PrbTotDL[i]
            
            # avg_throughput += max((demand - self.RRU_ThpDL_UE[i])/demand, 0)
            # avg_delay += max((self.DRB_Delay[i] - latency_requirment)/latency_requirment, 0)
            
        alpha = 1/100
        beta = 1/100
        reward = alpha * avg_throughput - beta * avg_delay
        
        #print("reward", reward)
        done = False

        return avg_throughput, avg_delay, avg_prbs, reward, done
    
    def caculate_regret(self, action, user_num):  #only for iperf/iperf3  #以最大化最小吞吐量的用户作为标准
        # reward = 0 if action == 0 else 0.0
        # print(self.RRU_PrbTotUL_UE1, self.RRU_PrbTotDL_UE1, self.RRU_PrbTotUL_UE2, self.RRU_PrbTotDL_UE2)
        # throuput = self.kpm_state[4] + self.kpm_state[5] # 70M...70000  UL600 1000
        # delay = self.kpm_state[3]  # 20ms 20000
        # 主要关注下行流量
        # max - min fairness：
        # 迭代过程：通常，使用迭代算法，其中以增量方式分配资源以提高最小吞吐量，直到无法进一步改进。
        # 优先级调度：在资源分配决策中，吞吐量最低的用户将获得更高的优先级。
        #min_throughput = min(self.RRU_ThpDL_UE1, self.RRU_ThpDL_UE2)
        # reward = min_throughput - self.prev_min_throughput
        sum_regret_throughput = 0
        sum_regret_dalay = 0
        sum_regret_bler = 0
        sum_regret_prbs = 0
        demand = 120
        latency_requirment = 200   #
        bler_requirment = 0.2
        C = 2   #to 
        for i in range(0, user_num):
            sum_regret_throughput += max((demand - self.RRU_ThpDL_UE[i])/demand, 0)
            sum_regret_dalay += max((self.DRB_Delay[i] - latency_requirment)/latency_requirment, 0)
            sum_regret_bler += max((self.BLER[i] - bler_requirment)/bler_requirment, 0)
            sum_regret_prbs += 1/(self.RRU_PrbTotDL[i]+C)
        alpha = 1/100
        beta = 0
        gama = 0
        regret = alpha * sum_regret_throughput + beta * sum_regret_dalay + gama * sum_regret_bler - sum_regret_prbs
        reward = -regret
        #print("reward", reward)

        #throuput = self.RRU_ThpDL_UE1
        #delay =
        ''' a = 0.001
        b = 0.02
        #reward = a * throuput - b * delay
        reward =
        info = {} # additional information '''
        # if it finished or not
        done = False

        #return sum_regret_throughput, sum_regret_dalay, sum_regret_bler, sum_regret_prbs, regret, done
        return sum_regret_throughput, sum_regret_dalay, sum_regret_bler, regret, done

    def render(self, mode='human'):
        print(f"State: {self.state}")





