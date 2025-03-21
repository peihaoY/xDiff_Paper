import argparse
import gym
import numpy as np
import os
import torch

import d4rl
from utils import utils
from utils.data_sampler import Data_Sampler
from utils.logger import logger, setup_logger
from torch.utils.tensorboard import SummaryWriter
import matplotlib.pyplot as plt

from env import icic_env
import time
import csv
import sys
import signal

from agents.ql_cm import CPQL as Agent    #这里将 agent 导入

def append_reward_to_csv(file_path, rewards, throughput, latancy, prbs, each_time, totel_times):
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        #if not file_exists:
        writer.writerow(['Reward', 'Throughput', 'Latancy', 'PRBs', 'Each_time', 'Totel_time'])
        #writer.writerow(['end', 'end', 'end', 'end', 'end', 'end'])
        for reward, throughput, latancy, prbs, each_time, totel_times in zip(rewards, throughput, latancy, prbs, each_time, totel_times):
            writer.writerow([reward, throughput, latancy, prbs, each_time, totel_times])
    print(f"数据已保存到 {file_path}")

def signal_handler(sig, frame):
    print("程序中断，正在保存数据...")
    append_reward_to_csv('rewards.csv', rewards_G, throughput_G, latancy_G, prbs_G, each_time_G, totel_times_G)
    sys.exit(0)

rewards_G = []
throughput_G = []
latancy_G = []
prbs_G = []
each_time_G = []
totel_times_G = []

online_hyperparameters = {
    'mujoco': {'lr': 3e-4, 'alpha': 0.05, 'eta': 1.0, 'num_epochs': 100, 'gn': 2.0, 'seed': 0},
}

ue_num = 3
user_split = [1, 1, 1]    #提高数据维度的可扩展性
gnb_num = 3
gnb_id_array = [3584, 3585, 3586]    # b210, n310, x310

# ue_num = 2
# user_split = [1, 1]    #提高数据维度的可扩展性
# gnb_num = 2
# gnb_id_array = [3584, 3586]    # b210, n310, x310

plt.ion()  
fig, ax1 = plt.subplots(1, 1, figsize=(10, 8))  

def train_agent(env, state_dim, action_dim, device, output_dir, args):
    agent = Agent(state_dim=state_dim,
                  action_dim=action_dim,
                  action_space = env.action_space,
                  rl_type = args.rl_type,
                  device=device,
                  discount=args.discount,
                  max_q_backup=args.max_q_backup,
                  lr=args.lr,
                  eta=args.eta,
                  alpha=args.alpha,
                  lr_decay=args.lr_decay,
                  lr_maxt=args.num_epochs,
                  grad_norm=args.gn,
                  q_mode=args.q_mode,
                  sampler=args.sampler,
                  expectile=args.expectile,
                  memory_size=args.memory_size,)

    writer = SummaryWriter(output_dir) 

    training_iters = 0
    max_timesteps = args.num_epochs * args.num_steps_per_epoch
    log_interval = int(args.eval_freq * args.num_steps_per_epoch)   # 5* 10

    utils.print_banner(f"Training Start", separator="*", num_star=90)

    signal.signal(signal.SIGINT, signal_handler)

    while (training_iters < max_timesteps+1):
        curr_epoch = int(training_iters // int(args.num_steps_per_epoch))
        done = False
        #state = env.reset()  
        state = [0]*ue_num*10
        episode_steps = 0
        episode_reward = 0

        # Online RL
        # Run for one whole episode
        total_start_time = time.time()
        while not done:  #这里是整个和GNB交互的过程
            roll_time_begain = time.time()
            # Updating the replay buffer
            if training_iters < args.online_start_steps:
                action = env.action_space.sample()   # 程序运行初期直接随便给action
                
            else:
                action = agent.sample_action(state)    #通过agent训练之后的action
            #next_state, reward, done, _ = env.step(action)   #从gnb获得信息
            #print("action", action)
            # ue_num = 2
            # user_split = {1, 1}    #提高数据维度的可扩展性
            # gnb_num = 2
            # gnb_id_array = [3584, 3586]    # b210, n310, x310

            env.send_action(action, 0, ue_num, gnb_num, user_split)  #for real system
            #time.sleep(0.1)++
            ue_mac  = env.get_all_state(gnb_id_array, ue_num)
            next_state = np.array(ue_mac).flatten()
            #print("next state", next_state)
            t, l, p, reward, done = env.caculate_reward(action, ue_num)
            print("Regret", reward)

            #print("state", state)
            agent.append_memory(state, action, reward, next_state, 1. - done)
            state = next_state
            episode_steps += 1
            episode_reward += reward

            rewards_G.append(reward)
            ax1.clear()
            ax1.plot(rewards_G, label='Regret')
            ax1.legend()
            plt.pause(0.01)

            throughput_G.append(t)
            latancy_G.append(l)
            prbs_G.append(p)
            roll_time_end = time.time()
            each_time_G.append(roll_time_end - roll_time_begain)
            totel_times_G.append(roll_time_end - total_start_time)

            # Training
            if training_iters >= args.online_start_steps:
                loss_metric = agent.train(agent.memory,
                                        batch_size=args.batch_size,
                                        log_writer=writer)
            else:
                loss_metric = None
            
            #print("##########################", loss_metric)
            training_iters += 1
            
            if loss_metric is not None:
                writer.add_scalar('Loss/bc_loss', np.mean(loss_metric['bc_loss']), training_iters)
                writer.add_scalar('Loss/ql_loss', np.mean(loss_metric['ql_loss']), training_iters)
                writer.add_scalar('Loss/actor_loss', np.mean(loss_metric['actor_loss']), training_iters)
                writer.add_scalar('Loss/critic_loss', np.mean(loss_metric['critic_loss']), training_iters)
            
            # Logging
            if training_iters % log_interval == 0:
                if loss_metric is not None:
                    utils.print_banner(f"Train step: {training_iters}", separator="*", num_star=90)
                    logger.record_tabular('Trained Epochs', curr_epoch)
                    logger.record_tabular('BC Loss', np.mean(loss_metric['bc_loss']))
                    logger.record_tabular('QL Loss', np.mean(loss_metric['ql_loss']))
                    logger.record_tabular('Actor Loss', np.mean(loss_metric['actor_loss']))
                    logger.record_tabular('Critic Loss', np.mean(loss_metric['critic_loss']))
                    logger.dump_tabular()
                    

                # Evaluating
                '''
                eval_res, eval_res_std, _, _ = eval_policy(agent, 
                                                            args.rl_type,
                                                            args.env_name, 
                                                            args.seed,
                                                            eval_episodes=args.eval_episodes)
                done = True

                writer.add_scalar('Eval/avg', eval_res, training_iters)
                writer.add_scalar('Eval/std', eval_res_std, training_iters)

                logger.record_tabular('Average Episodic Reward', eval_res)
                logger.dump_tabular()
                '''
                
                if args.save_checkpoints:
                    agent.save_model(output_dir, curr_epoch)

    agent.save_model(output_dir, curr_epoch)
    plt.ioff()
    plt.show()
    writer.close()


# Runs policy for [eval_episodes] episodes and returns average reward
# A fixed seed is used for the eval environment
def eval_policy(policy, rl_type, env_name, seed, eval_episodes=10):
    eval_env = gym.make(env_name)
    eval_env.seed(seed + 100)

    scores = []
    for _ in range(eval_episodes):
        traj_return = 0.
        state, done = eval_env.reset(), False
        while not done:
            action = policy.sample_action(np.array(state))
            state, reward, done, _ = eval_env.step(action)
            traj_return += reward
        scores.append(traj_return)

    avg_reward = np.mean(scores)
    std_reward = np.std(scores)

    return avg_reward, std_reward, 0, 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    ### Experimental Setups ###
    parser.add_argument('--device', default=0, type=int) 

    parser.add_argument('--rl_type', default="online", type=str, help='offline or online RL tasks (default: online)') 
    parser.add_argument("--q_mode", default="q", type=str, help='q for CPQL and q_v for CPIQL') 

    parser.add_argument("--env_name", default="intercell_interference", type=str, help='Mujoco Gym environment') 

    parser.add_argument("--dir", default="results", type=str) 
    parser.add_argument('--save_checkpoints', action='store_true')

    parser.add_argument("--num_steps_per_epoch", default=10, type=int)
    parser.add_argument("--online_start_steps", default=10, type=int)
    parser.add_argument("--memory_size", default=1e3, type=int)
    parser.add_argument("--batch_size", default=16, type=int, help='batch size (default: 256)')
    parser.add_argument("--lr_decay", action='store_true')
    parser.add_argument("--discount", default=0.99, type=float, help='discount factor for reward (default: 0.99)')

    args = parser.parse_args()

    if args.rl_type == 'online' and args.q_mode == 'q_v':
        raise AssertionError("CPIQL is not supported for online RL tasks!")

    args.device = f"cuda:{args.device}" if torch.cuda.is_available() else "cpu"
    args.output_dir = f'{args.dir}'

    args.num_epochs = online_hyperparameters['mujoco']['num_epochs']
    args.seed = online_hyperparameters['mujoco']['seed']
    args.lr = online_hyperparameters['mujoco']['lr']
    args.eta = online_hyperparameters['mujoco']['eta']
    args.alpha = online_hyperparameters['mujoco']['alpha']
    args.gn = online_hyperparameters['mujoco']['gn']
    args.expectile = 0

    args.max_q_backup = False
    args.reward_tune = 'no'
    args.sampler = 'onestep'

    args.eval_freq = 5
    args.eval_episodes = 10 
    #log_interval = int(args.eval_freq * args.num_steps_per_epoch)

    # Setup Logging
    
    file_name = 'QL' if args.q_mode == 'q' else 'IQL'
    if args.q_mode == 'q_v':
        file_name += f'|tau-{args.expectile}'
    file_name += f'|{args.seed}'
    file_name += f"|alpha-{args.alpha}|eta-{args.eta}"

    file_name += f'|sampler_{args.sampler}'

    file_name += f'|test_qnorm'

    results_dir = os.path.join(args.output_dir, args.rl_type, args.env_name, file_name)

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    utils.print_banner(f"Saving location: {results_dir}")
    
    # if os.path.exists(os.path.join(results_dir, 'variant.json')):
    #     raise AssertionError("Experiment under this setting has been done!")

    variant = vars(args)
    variant.update(version=f"CMQL")

    #env = gym.make(args.env_name)
    env = icic_env()

    
    #env.seed(args.seed)
    #torch.manual_seed(args.seed)
    #np.random.seed(args.seed)

    #state_dim = env.observation_space.shape[0]
    #action_dim = env.action_space.shape[0] 

    state_dim = ue_num*10
    print("state_dim", state_dim)
    action_dim = ue_num*10 #every action belongs to (-1, 1)

    env.initlize(ue_num, action_dim)
    env.init_file()
    
    variant.update(state_dim=state_dim)
    variant.update(action_dim=action_dim)
    setup_logger(os.path.basename(results_dir), variant=variant, log_dir=results_dir)
    utils.print_banner(f"Env: icic_env, state_dim: {state_dim}, action_dim: {action_dim}")



    train_agent(env,
                state_dim,
                action_dim,
                args.device,
                results_dir,
                args)
    
