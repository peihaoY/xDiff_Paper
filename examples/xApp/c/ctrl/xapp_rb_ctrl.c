/*
 * Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The OpenAirInterface Software Alliance licenses this file to You under
 * the OAI Public License, Version 1.1  (the "License"); you may not use this file
 * except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.openairinterface.org/?page_id=698
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *-------------------------------------------------------------------------------
 * For more information about the OpenAirInterface (OAI) Software Alliance:
 *      contact@openairinterface.org
 */

#include "../../../../src/xApp/e42_xapp_api.h"
#include "../../../../src/sm/rc_sm/ie/ir/ran_param_struct.h"
#include "../../../../src/sm/rc_sm/ie/ir/ran_param_list.h"
#include "../../../../src/util/time_now_us.h"
#include "../../../../src/util/alg_ds/ds/lock_guard/lock_guard.h"
#include "../../../../src/sm/rc_sm/rc_sm_id.h"
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>

int nodes_id = 0;
int nb_id = 0;

typedef enum{
    DRX_parameter_configuration_7_6_3_1 = 1,
    SR_periodicity_configuration_7_6_3_1 = 2,
    SPS_parameters_configuration_7_6_3_1 = 3,
    Configured_grant_control_7_6_3_1 = 4,
    CQI_table_configuration_7_6_3_1 = 5,
    Slice_level_PRB_quotal_7_6_3_1 = 6,
    Interference_PRB_quotal_7_6_3_1 = 7,    //peihao
} rc_ctrl_service_style_2_act_id_e;

static
e2sm_rc_ctrl_hdr_frmt_1_t gen_rc_ctrl_hdr_frmt_1(ue_id_e2sm_t ue_id, uint32_t ric_style_type, uint16_t ctrl_act_id)
{
  e2sm_rc_ctrl_hdr_frmt_1_t dst = {0};

  // 6.2.2.6
  dst.ue_id = cp_ue_id_e2sm(&ue_id);

  dst.ric_style_type = ric_style_type;
  dst.ctrl_act_id = ctrl_act_id;

  return dst;
}

static
e2sm_rc_ctrl_hdr_t gen_rc_ctrl_hdr(e2sm_rc_ctrl_hdr_e hdr_frmt, ue_id_e2sm_t ue_id, uint32_t ric_style_type, uint16_t ctrl_act_id)
{
  e2sm_rc_ctrl_hdr_t dst = {0};

  if (hdr_frmt == FORMAT_1_E2SM_RC_CTRL_HDR) {
    dst.format = FORMAT_1_E2SM_RC_CTRL_HDR;
    dst.frmt_1 = gen_rc_ctrl_hdr_frmt_1(ue_id, ric_style_type, ctrl_act_id);
  } else {
    assert(0!=0 && "not implemented the fill func for this ctrl hdr frmt");
  }

  return dst;
}

typedef enum {
    RRM_Policy_Ratio_List_8_4_3_7 = 1,
    RRM_Policy_Ratio_Group_8_4_3_7 = 2,
    Du_Map_8_4_3_7 = 3,
    //Int_Map_8_4_3_7 = 4,
} interference_PRB_quota_param_id_e;

static
void gen_rrm_policy_ratio_group(lst_ran_param_t* RRM_Policy_Ratio_Group,
                                float du_ratio_prb[10])
                                //int num_rbg)
                                //int a[10])
{
  // RRM Policy Ratio Group, STRUCTURE (RRM Policy Ratio List -> RRM Policy Ratio Group)
  // lst_ran_param_t* RRM_Policy_Ratio_Group = &RRM_Policy_Ratio_List->ran_param_val.lst->lst_ran_param[0];
  // RRM_Policy_Ratio_Group->ran_param_id = RRM_Policy_Ratio_Group_8_4_3_6;
  RRM_Policy_Ratio_Group->ran_param_struct.sz_ran_param_struct = 10;
  RRM_Policy_Ratio_Group->ran_param_struct.ran_param_struct = calloc(10, sizeof(seq_ran_param_t));
  assert(RRM_Policy_Ratio_Group->ran_param_struct.ran_param_struct != NULL && "Memory exhausted");
  // RRM Policy, STRUCTURE (Rgen_rrm_policy_ratio_listRM Policy Ratio Group -> RRM Policy)
  // seq_ran_param_t* RRM_Policy = &RRM_Policy_Ratio_Group->ran_param_struct.ran_param_struct[0];
  for (int i = 0; i < 10; i ++){
    seq_ran_param_t* Du_Map = &RRM_Policy_Ratio_Group->ran_param_struct.ran_param_struct[i];
    Du_Map->ran_param_id = Du_Map_8_4_3_7;
    Du_Map->ran_param_val.type = ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE;
    Du_Map->ran_param_val.flag_false = calloc(1, sizeof(ran_parameter_value_t));
    assert(Du_Map->ran_param_val.flag_false != NULL && "Memory exhausted");
    Du_Map->ran_param_val.flag_false->type = INTEGER_RAN_PARAMETER_VALUE;
    //Du_Map->ran_param_val.flag_false->int_ran = du_ratio_prb;
    //for (int i = 0; i < 10; i++) {
    Du_Map->ran_param_val.flag_false->real_ran = du_ratio_prb[i];
    printf("%f\n", Du_Map->ran_param_val.flag_false->real_ran);
    // }
  }

/*
  seq_ran_param_t* int_Map = &RRM_Policy_Ratio_Group->ran_param_struct.ran_param_struct[1];
  int_Map->ran_param_id = Int_Map_8_4_3_7;
  int_Map->ran_param_val.type = ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE;
  int_Map->ran_param_val.flag_false = calloc(1, sizeof(ran_parameter_value_t));
  assert(int_Map->ran_param_val.flag_false != NULL && "Memory exhausted");
  int_Map->ran_param_val.flag_false->type = INTEGER_RAN_PARAMETER_VALUE;
  //Du_Map->ran_param_val.flag_false->int_ran = du_ratio_prb;
  int_Map->ran_param_val.flag_false->int_ran = (int *)malloc(10 * sizeof(int));
  for (int i = 0; i < 10; i++) {
    int_Map->ran_param_val.flag_false->int_ran[i] = a[i];
    printf("%d\n", int_Map->ran_param_val.flag_false->int_ran[i]);
  }
*/
  //free(int_Map->ran_param_val.flag_false->int_ran);

  return;
}

static
void gen_rrm_policy_ratio_list(seq_ran_param_t* RRM_Policy_Ratio_List)
{
  int a, num_ue, num_gnb;
  //float c[3][10] = {0};
  float **c = NULL; // 用于动态存储数据
  char line[1024];
  int num_rbg = 10;

  FILE *file = fopen("rlflexric/dudata/ctrl.csv", "r");
  if (file == NULL) {
      perror("Error opening file");
      return 1;
  }

  if (nb_id == 3584){
    nodes_id = 0;
  } else if (nb_id == 3586)
  {
    nodes_id = 1;
  }else if (nb_id == 3585)
  {
    nodes_id = 2;
  }else{
    printf("没有这类node_id!\n");
  }
  

  // 第一行处理 a 和 b
  int gnb_ue_num[3];
  if (fgets(line, sizeof(line), file)) {
      sscanf(line, "%d, %d, %d, %d, %d, %d", &a, &num_ue, &num_gnb, &gnb_ue_num[0], &gnb_ue_num[1], &gnb_ue_num[2]);
  } else {
      printf("文件内容为空或格式错误。\n");
      fclose(file);
      return 1;
  }
  printf("nodes_id = %d \n", nodes_id);
  //if(nodes_id = 0)//这里0表示gnb1, 1表示gnb2
  // 为二维数组分配内存
  int du_num_ue;
  du_num_ue = gnb_ue_num[nodes_id];
  printf("du_num_ue = %d \n", du_num_ue);

  int first_ue_id = 0;
  for (int i = 0; i < nodes_id; i++){
    first_ue_id += gnb_ue_num[i];
  }
  c = malloc(du_num_ue * sizeof(float *));
  for (int i = 0; i < du_num_ue; i++) {
    c[i] = malloc(10 * sizeof(float)); // 每行固定 10 列
  }

  printf("first_ue_id = %d \n", first_ue_id);

  for (int i = 0; i < first_ue_id; i++) {
    if (!fgets(line, sizeof(line), file)) {
      printf("数据行不足。\n");
      fclose(file);
      return 1;
    }
  }

  // 读取后续行的数据
  for (int i = 0; i < du_num_ue; i++) {
    if (fgets(line, sizeof(line), file)) {
      // 使用 sscanf 解析一行数据并赋值到二维数组 c
        sscanf(line, "%f,%f,%f,%f,%f,%f,%f,%f,%f,%f",
          &c[i][0], &c[i][1], &c[i][2], &c[i][3], &c[i][4],
          &c[i][5], &c[i][6], &c[i][7], &c[i][8], &c[i][9]);
    } else {
      printf("数据行不足。\n");
      fclose(file);
      return 1;
    }
  }
  fclose(file);
  
  //int num_ue = 2;
  // seq_ran_param_t* RRM_Policy_Ratio_List =  &dst.ran_param[0];
  RRM_Policy_Ratio_List->ran_param_id = RRM_Policy_Ratio_List_8_4_3_7;
  RRM_Policy_Ratio_List->ran_param_val.type = LIST_RAN_PARAMETER_VAL_TYPE;
  RRM_Policy_Ratio_List->ran_param_val.lst = calloc(1, sizeof(ran_param_list_t));
  assert(RRM_Policy_Ratio_List->ran_param_val.lst != NULL && "Memory exhausted");
  RRM_Policy_Ratio_List->ran_param_val.lst->sz_lst_ran_param = du_num_ue;
  RRM_Policy_Ratio_List->ran_param_val.lst->lst_ran_param = calloc(du_num_ue, sizeof(lst_ran_param_t));
  assert(RRM_Policy_Ratio_List->ran_param_val.lst->lst_ran_param != NULL && "Memory exhausted");

  //这三个数组的长度和该gnb中的ue数量相关
  /*
  float ratio_prb[num_ue][10]; 
  srand(time(NULL));
  for (int i = 0; i < num_ue; i++) {
    for (int j =0; j < 10; j++){
      ratio_prb[i][j] = ((float)rand() / RAND_MAX) * 2 - 1; // 生成 -1 到 1 之间的随机小数
      //printf("%f\n", ratio_prb[i][j]);
    }
  }

  int ratio_prb[10];
  for (int i = 0; i < 10; i++){
    ratio_prb[i] = rand() %2;
  }  */

  for (int i = 0; i < du_num_ue; i++) {
    gen_rrm_policy_ratio_group(&RRM_Policy_Ratio_List->ran_param_val.lst->lst_ran_param[i],
                               c[i]);
  }

  for (int i = 0; i < du_num_ue; i++) {
    free(c[i]);
  }
  free(c);

  return;
}

static
e2sm_rc_ctrl_msg_frmt_1_t gen_rc_ctrl_msg_frmt_1_slice_level_PRB_quota()
{
  e2sm_rc_ctrl_msg_frmt_1_t dst = {0};

  // RRM Policy Ratio List, LIST
  dst.sz_ran_param = 1;
  dst.ran_param = calloc(1, sizeof(seq_ran_param_t));
  assert(dst.ran_param != NULL && "Memory exhausted");
  gen_rrm_policy_ratio_list(&dst.ran_param[0]);

  return dst;
}

static
e2sm_rc_ctrl_msg_t gen_rc_ctrl_msg(e2sm_rc_ctrl_msg_e msg_frmt)
{
  e2sm_rc_ctrl_msg_t dst = {0};

  if (msg_frmt == FORMAT_1_E2SM_RC_CTRL_MSG) {
    dst.format = msg_frmt;
    dst.frmt_1 = gen_rc_ctrl_msg_frmt_1_slice_level_PRB_quota();
  } else {
    assert(0!=0 && "not implemented the fill func for this ctrl msg frmt");
  }

  return dst;
}

static
ue_id_e2sm_t gen_rc_ue_id(ue_id_e2sm_e type)
{
  ue_id_e2sm_t ue_id = {0};
  if (type == GNB_UE_ID_E2SM) {
    ue_id.type = GNB_UE_ID_E2SM;
    // TODO
    ue_id.gnb.amf_ue_ngap_id = 0;
    ue_id.gnb.guami.plmn_id.mcc = 1;
    ue_id.gnb.guami.plmn_id.mnc = 1;
    ue_id.gnb.guami.plmn_id.mnc_digit_len = 2;
    ue_id.gnb.guami.amf_region_id = 0;
    ue_id.gnb.guami.amf_set_id = 0;
    ue_id.gnb.guami.amf_ptr = 0;
  } else {
    assert(0!=0 && "not supported UE ID type");
  }
  return ue_id;
}

int main(int argc, char *argv[])
{
  fr_args_t args = init_fr_args(argc, argv);
  //defer({ free_fr_args(&args); });

  //Init the xApp
  init_xapp_api(&args);
  sleep(1);

  e2_node_arr_xapp_t nodes = e2_nodes_xapp_api();
  defer({ free_e2_node_arr_xapp(&nodes); });
  assert(nodes.len > 0);
  printf("Connected E2 nodes = %d\n", nodes.len);

  ////////////
  // START RC
  ////////////

  // RC Control
  // CONTROL Service Style 2: Radio Resource Allocation Control
  // Action ID 6: Slice-level PRB quota
  // E2SM-RC Control Header Format 1
  // E2SM-RC Control Message Format 1
  rc_ctrl_req_data_t rc_ctrl = {0};
  ue_id_e2sm_t ue_id = gen_rc_ue_id(GNB_UE_ID_E2SM);

  rc_ctrl.hdr = gen_rc_ctrl_hdr(FORMAT_1_E2SM_RC_CTRL_HDR, ue_id, 3, Interference_PRB_quotal_7_6_3_1);
  //c_ctrl.msg = gen_rc_ctrl_msg(FORMAT_1_E2SM_RC_CTRL_MSG);

  int64_t st = time_now_us();

  for(size_t i = 0; i < nodes.len; ++i){
    nb_id = nodes.n[i].id.nb_id.nb_id;
    rc_ctrl.msg = gen_rc_ctrl_msg(FORMAT_1_E2SM_RC_CTRL_MSG);
    control_sm_xapp_api(&nodes.n[i].id, SM_RC_ID, &rc_ctrl);
  }
  printf("[xApp]: Control Loop Latency: %ld us\n", time_now_us() - st);
  free_rc_ctrl_req_data(&rc_ctrl);

  ////////////
  // END RC
  ////////////

  sleep(5);


  //Stop the xApp
  while(try_stop_xapp_api() == false)
    usleep(1000);

  printf("Test xApp run SUCCESSFULLY\n");

}