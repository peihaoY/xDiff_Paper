# xDiff: Online Diffusion Model for Collaborative Inter-Cell Interference Management in O-RAN
Open Radio Access Network (O-RAN) is a key architectural paradigm for 5G and beyond cellular networks, enabling the adoption of intelligent and efficient resource management solutions. Meanwhile, diffusion models have demonstrated remarkable capabilities in image and video generation, making them attractive for network optimization tasks. 

In this paper, we propose xDiff, a diffusion-based reinforcement learning (RL) framework for inter-cell interference management (ICIM) in O-RAN. We first formulate ICIM as a resource allocation optimization problem aimed at maximizing a user-defined reward function and then develop an online learning solution by integrating a diffusion model into an RL framework for near-real-time policy generation. Particularly, we introduce a novel metric, preference values, as the policy representation to enable efficient policy-guided resource allocation within O-RAN distributed units (DUs). 

We implement xDiff on a 5G testbed consisting of three cells and a set of smartphones in two small cell scenarios. Experimental results demonstrate that xDiff outperforms state-of-the-art ICIM approaches, highlighting the potential of diffusion models for online optimization of O-RAN.

## Getting Started
### Minimum hardware requirements:
- Laptop/Desktop/Server for OAI CN5G and OAI gNB
    - Operating System: Ubuntu 22.04 LTS
    - CPU: 12 cores x86_64 @ 3.5 GHz
    - RAM: 32 GB
- [USRP N300](https://www.ettus.com/all-products/USRP-N300/) and [USRP X300](https://www.ettus.com/all-products/x300-kit/) and [USRP B210](https://www.ettus.com/all-products/ub210-kit/)

### Software reference:
Our system consists of the configuration of RIC + xApp, 5G O-RAN, and 5G Core. xDiff has developed its own architecture and algorithms based on [Flexric](https://gitlab.eurecom.fr/mosaic5g/flexric), [OAI cn5g](https://gitlab.eurecom.fr/oai/cn5g), and [openairinterface5G](https://gitlab.eurecom.fr/oai/openairinterface5g).

## Dependencies and Code Clone

## 1. RIC + xApp Setup (https://github.com/peihaoY/xDiff_Paper)

### 1.1 python conv requirement
1. First, ensure that Python and pip are installed on the target computer. You can check this by running the following commands:
```bash
python --version  # or python3 --version
pip --version
```
If Python is not installed, please download and install it from the official Python website.

2. In the target directory, create and activate a new virtual environment and install dependencies. 
```bash
python -m venv myenv  # or python3 -m venv myenv
# Activate the virtual environment:
source myenv/bin/activate
```
Copy the requirements.txt file to your target computer's directory. Then, install all the dependencies using the following command:
```bash
conda env create -f environment.yml
```


### 1.2 RIC prerequisites

Please find the CMAKE and SWIG dependencies on the [Flexric website](https://gitlab.eurecom.fr/mosaic5g/flexric).

Note: - GCC (gcc-10)      *gcc-11 is not currently supported.

### 1.3 Clone the RIC +xApp code, build and install it. 

* Clone code and make install
```bash
# Get xDiff_xApp source code
git clone https://github.com/peihaoY/xDiff_Paper ~/xDiff_xApp  
# Build RIC
cd xDiff_xApp && mkdir build && cd build && cmake .. && make -j8 
# You can install the Service Models (SM) in your computer via:
sudo make install
```

## 2. O-RAN/gNB Setup  (https://github.com/peihaoY/xDiff_gnb)

### 2.1 5G Core Setup

Please install and configure OAI CN5G as described here: [OAI 5G NR CN tutorial](https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_OAI_CN5G.md)




### 2.2 Pre-requisites

Please find the UHD and other requirements on the [OAI gNB tutorial](https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_COTS_UE.md).

 <!-- Build UHD from source
```bash
sudo apt install -y autoconf automake build-essential ccache cmake cpufrequtils doxygen ethtool g++ git inetutils-tools libboost-all-dev libncurses-dev libusb-1.0-0 libusb-1.0-0-dev libusb-dev python3-dev python3-mako python3-numpy python3-requests python3-scipy python3-setuptools python3-ruamel.yaml

git clone https://github.com/EttusResearch/uhd.git ~/uhd
cd ~/uhd
git checkout v4.7.0.0
cd host
mkdir build
cd build
cmake ../
make -j $(nproc)
make test # This step is optional
sudo make install
sudo ldconfig
sudo uhd_images_downloader
``` -->
### 2.3 Install and Build xDiff_gNB

```bash
# Get xDiff_ORAN source code
git clone https://github.com/peihaoY/xDiff_gnb.git ~/xDiff_ORAN
cd ~/xDiff_gnb

# Install OAI dependencies and build ORAN
cd ~/xDiff_gnb/cmake_targets
./build_oai -I
./build_oai -w USRP --ninja --build-e2 --gNB -C
```

- Smartphone set up
The COTS UE can now search for the network. You can find how to connect UE to gNB on [srsRAN website](https://docs.srsran.com/projects/project/en/latest/tutorials/source/cotsUE/source/index.html).

### 2.4 Separate O-CU and  O-DU

Please find how to separate O-CU and  O-DU on [F1AP website](https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/F1AP/F1-design.md?ref_type=heads).


## Modified code structure
In both the RAN and RIC systems, there are numerous code files involved. Below, I have listed the files that I modified or added as part of implementing xDiff. The structure is as follows. For detailed comments and further information, please refer directly to the code.

### 1. xDiff_xApp

```bash
.
├── diffusion                        # source code for diffusion policy algrithom
│   ├── main.py   
│   ├── env.py              
    │   agent
    │   ├── ql_cm
    │   ├── diffusion
├── examples                         # xApp for RAN Slicing and information monitor         
│   ├── ric                          # RIC including E2 interface
│   └── xApp                         # source code for xApps
    │   c                            # our xApps based on C code
        │   ctrl            
        │   ├── mac_ctrl.c           # test code for mac layer control
        │   ├── xapp_combin_ctrl.c   # Source code for xDiff
    │   ├── python3                  # external python code examples for xApps
├── dudata                         # data storage
│   ├── KPM_UE.txt             
│   ├── interference_map.txt         # sent preference value to each DU         
│   ├── xapp_db_               
│   ├── kpm.py                       # show KPM data
│   ├── mac.py                       # show MAC-Layer data
│   └── rewards.csv            
```

### 2. xDiff_gNB

```bash
.
├── openair2                     
│   ├── E2AP                                    # source code for E2 interface
    │   ├── RAN_FUNCTION                   
        │   ├── CUSTOMIZED                      # monitor functions
            │   ├── ran_func_mac.c         
            │   └── ran_func_kpm.c         
        │   └── O-RAN                           # control service functions
            │   ├── rc_ctrl_service_style_2.c   # xDiff 
│   ├── LAYER2                                  # MAC layer funtions
    │   ├── NR_MAC_gNB                          # MAC scheduler      
        │   ├── gNB_scheduler_dlsch.c           # source code for downlink mac scheduler
```
### 3. Extend xDiff
If you wish to extend 'xDiff', please review the modification sections and comments in the code above. These will guide you through quickly getting started with implementing your own online learning algorithm in a new xApp.

## Run xDiff
## 1. On 5G Core server:
```bash
cd ~/oai-cn5g
docker compose up -d
```
## 2. On xDiff_gnb server:

### 2.1 Run O-CU
```bash
cd ~/xDiff_gnb
sudo cmake_targets/ran_build/build/nr-softmodem --sa -O gnb-cu.sa.band78.106prb.conf
```

### 2.1 Run 3 O-DU-O-RU (Cells)
If you are using the USRP, please directly install and run the following command. If you are using a different model of RU, please modify your device address accordingly.
```bash
cd ~/xDiff_gnb
# USRP N310
sudo cmake_targets/ran_build/build/nr-softmodem -O gnb-du.sa.band78.fr1.106PRB.2x2.usrpn300.conf --sa --usrp-tx-thread-config 1
# USRP B210
sudo cmake_targets/ran_build/build/nr-softmodem -O gnb-du.sa.band78.fr1.106PRB.usrpb210.conf --sa --usrp-tx-thread-config 1  -E --continuous-tx
# USRP X310
sudo cmake_targets/ran_build/build/nr-softmodem -O gnb-du.sa.band78.fr1.106PRB.2x2.usrpx300.conf --sa --usrp-tx-thread-config 1 -E --continuous-tx

```


### 2.2 Check UEs' successfully connected and generate demand:
You can use the following commands to check the 5G Core's AMF, UPF, and other components.
```bash
docker logs oai-amf -f
docker logs oai-upf -f
```

Check UEs' information:

<!-- Connection #0 to host 192.168.70.133 left intact
[2024-09-07 19:34:15.134] [amf_sbt] [info] Get response with HTTP code (200)
[2024-09-07 19:34:15.134] [amf_sbt] [info] Response body {"upCnxState": "DEACTIVATED"}
[2024-09-07 19:34:15.134] [amf_app] [debug] Parsing the message with the Simple Parser
[2024-09-07 19:34:15.134] [amf_sbt] [info] JSON part {"upCnxState": "DEACTIVATED"}
[2024-09-07 19:34:15.134] [amf_sbt] [debug] UP Deactivation
[2024-09-07 19:34:15.134] [amf_app] [debug] Trigger process response: Set promise with ID 37 to ready
[2024-09-07 19:34:15.134] [amf_server] [debug] Got result for PDU Session Id 5
[2024-09-07 19:34:15.134] [amf_n2] [debug] Removed UE NGAP context with amf_ue_ngap_id 30
[2024-09-07 19:34:15.134] [amf_n2] [debug] Removed UE NGAP context with ran_ue_ngap_id 6, gnb_id 57344
[2024-09-07 19:34:15.134] [ngap] [debug] Free NGAP Message PDU -->

```bash
[2024-09-07 19:34:15.902] [amf_app] [info]

|----------------------gNBs Information:--------------|
| Index | Status    | Global Id | gNB Name | PLMN     |
|-------|-----------|-----------|----------|----------|
| 1     | Connected | 0xE000    | gNB-OAI  | 001,01   |
|-----------------------------------------------------|


|-----------------------------------------------------------UEs Information:-------------------------------------------
| Index | 5GMM State       | IMSI            | GUTI              | RAN UE NGAP ID | AMF UE NGAP ID | PLMN   | Cell Id   |
|-------|------------------|-----------------|-------------------|----------------|----------------|--------|-----------|
| 1     | 5GMM-REGISTERED  | 001010000000001 | 00101010041000003 | 0x03           | 0x1F           | 001,01 | 0xE00000  |
| 2     | 5GMM-REGISTERED  | 001010000000002 | 00101010041000001 | 0x01           | 0x01           | 001,01 | 0xE00000  |
| 3     | 5GMM-REGISTERED  | 001010000000003 | 00101010041000006 | 0x06           | 0x06           | 001,01 | 0xE00000  |
| 4     | 5GMM-REGISTERED  | 001010000000004 | 00101010041000011 | 0x18           | 0x18           | 001,01 | 0xE00000  |
| 5     | 5GMM-REGISTERED  | 001010000000005 | 00101010041000012 | 0x14           | 0x14           | 001,01 | 0xE00000  |
| 6     | 5GMM-REGISTERED  | 001010000000006 | 00101010041000010 | 0x04           | 0x04           | 001,01 | 0xE00000  |
| 7     | 5GMM-REGISTERED  | 001010000000007 | 00101010041000004 | 0x0A           | 0x0A           | 001,01 | 0xE00000  |
| 8     | 5GMM-REGISTERED  | 001010000000008 | 00101010041000002 | 0x02           | 0x02           | 001,01 | 0xE00000  |
| 9     | 5GMM-REGISTERED  | 001010000000009 | 00101010041000009 | 0x0A           | 0x0A           | 001,01 | 0xE00000  |
| 10    | 5GMM-REGISTERED  | 001010000000010 | 00101010041000007 | 0x07           | 0x07           | 001,01 | 0xE00000  |
------------------------------------------------------------------------------------------------------
```
<!-- [2024-09-07 19:34:16.077] [sctp] [info] [Assoc_id 6, Socket 9] Received a message (length 147) from port 50209, on stream 1, PPID 60
[2024-09-07 19:34:16.077] [ngap] [debug] Handling SCTP payload from SCTP Server on assoc_id (6), stream_id (1), instreams (2), outstreams (2)
[2024-09-07 19:34:16.077] [ngap] [debug] Decoded NGAP message, procedure code 15, present 1 -->
You can generate traffic by accessing websites, streaming videos, downloading content, and more through the UE. Additionally, you can create traffic demands using iperf.

Run Iperf on UE to generate demand:
```bash
docker exec -it oai-ext-dn bash
iperf -u -t 86400 -i 1 -fk -B 192.168.70.135 -b 10M -c 10.0.0.2
```
## 3. On RIC+xApp server:
### 3.1 Start the nearRT-RIC
```bash
./xDiff_xApp/build/examples/ric/nearRT-RIC
```

### 3.2 Start xApps

Start the xDiff xApp

```bash
./xDiff_xApp/build/examples/xApp/c/ctrl/xapp_combin_ctrl
```
### 3.3 Start testing our algrithom
* To evaluate xDiff in your host:
```bash
python /xDiff_xApp/diffusion/main.py    # or python3 /xDiff_xApp/diffusion/main.py
```

* Here is a simple test case:
```bash
------------------------------------------------------------
Env: ICIM_env, state_dim: 30, action_dim: 30
******************************************************************************************
Training Start

24-11-22.18:46|[QL|alpha-0.05|eta-1.0|] --------------  -----------
24-11-22.18:46|[QL|alpha-0.05|eta-1.0|] Trained Epochs  0
                                        BC Loss         0.28673
                                        QL Loss         0.044308
                                        Actor Loss      0.0586445
                                        Critic Loss     7.39261e-06
24-11-22.18:46|[QL|alpha-0.05|eta-1.0|] --------------  -----------
                                        --------------  -----------

```

* Results will be saved in floder [dudata]
    - dudata/ `KPM_UE.txt`, `interference_map.txt`, `xapp_db_`  
    Please note that xapp_db_ is a compressed file. Be sure to extract it first before reviewing the contents.
    - diffusion/ `rewards.csv` 

For example, you can get preference values as following:
```bash
+------------+-------+-------+-------+-------+-------+-------+-------+
| RBG index  |   1   |   2   |   3   |   4   |   5   |   6   |
+------------+-------+-------+-------+-------+-------+-------+-------+
| UE₁ ∈ gNB₁ |  0.49 | -0.82 |  0.76 |  0.55 |  0.26 |  0.81 |
| UE₂ ∈ gNB₂ | -0.51 | -0.20 | -0.87 | -0.47 | -0.37 |  0.32 |
| UE₃ ∈ gNB₃ | -0.57 |  0.39 |  0.83 | -0.69 | -0.66 | -0.66 |
+------------+-------+-------+-------+-------+-------+-------+-------+
```

## Citation
If you use our code in your research, please cite our paper:
```bash
Coming soon...
```

## Getting help

If you encounter a bug or have any questions regarding the paper, the code or the setup process, please feel free to contact us: phyan@msu.edu
