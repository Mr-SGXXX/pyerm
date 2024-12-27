# MIT License

# Copyright (c) 2024 Yuxuan Shao

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Version: 0.3.3

import pandas as pd
import streamlit as st
import os
from PIL import Image
import re
import io
import typing

from pyerm.database.dbbase import Database
from pyerm.database.utils import get_result_statistics, get_result_statistics_by_ids
from pyerm.database.utils import method_id2remark_name, data_id2remark_name, experiment_remark_name2id
from pyerm.database.utils import method_remark_name2id, data_remark_name2id
from pyerm.webUI import PYERM_HOME
from pyerm.webUI.utils import boxplot, violinplot, lineplot, barplot

def analysis():
    title()
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        db = Database(st.session_state.db_path, output_info=False)
        analysis_task = sidebar_select_analysis()
        if analysis_task == st.session_state.lm["analysis.single_setting_analysis_text"]:
            task, method, method_id, dataset, dataset_id = select_setting(db)
            st.write('---')
            single_setting_analysis(db, task, method, method_id, dataset, dataset_id)
            
        elif analysis_task == st.session_state.lm["analysis.multi_setting_analysis_text"]:
            task, method, method_id, dataset, dataset_id = select_setting(db)
            if task != st.session_state.cur_analysis_task:
                st.session_state.recorded_analysis_setting = []
                st.session_state.cur_analysis_task = task
            if st.button(st.session_state.lm["analysis.multi_setting_record_cur_setting_button"], key='add_setting'):
                if not (method, method_id, dataset, dataset_id) in st.session_state.recorded_analysis_setting:
                    st.session_state.recorded_analysis_setting.append((method, method_id, dataset, dataset_id))
                    st.rerun()
            st.write('---')
            multi_setting_analysis(db)
            
    if st.sidebar.button(st.session_state.lm["app.refresh"], key='refresh'):
        st.rerun()
            
def single_setting_analysis(db, task, method, method_id, dataset, dataset_id):
    st.write(st.session_state.lm["analysis.single_setting_analysis.statistics_title"])
    result_statistics, same_setting_ids = get_result_statistics(db, task, method, method_id, dataset, dataset_id)
    num_records = len(same_setting_ids)
    if result_statistics is not None:
        st.dataframe(result_statistics, use_container_width=True)
        st.write(st.session_state.lm["analysis.single_setting_analysis.statistics_notice"].format(NUM_RECORDS=num_records))
    else:
        st.write(st.session_state.lm["analysis.single_setting_analysis.statistics_no_result_found"])
        return
    remarked_list = db[f'experiment_list'].select('remark', where=f'id in ({",".join(same_setting_ids)}) AND remark IS NOT NULL')
    remarked_list = [remark[0] for remark in remarked_list]
    # remarked_list = []
    # for id in same_setting_ids:
    #     remark = db[f'experiment_list'].select('remark', where=f'id={id}')[0][0]
    #     if remark is not None:
    #         remarked_list.append(remark)
    cols = st.columns(2)
    with cols[0]:
        st.write(st.session_state.lm["analysis.single_setting_analysis.statistics_chart_title"])
        plot_type = st.selectbox(st.session_state.lm["analysis.single_setting_analysis.statistics_chart_select"], ['Boxplot', 'Violinplot', 'Lineplot', 'Barplot'], index=0)
        single_setting_plot(db, task, same_setting_ids, plot_type)
    with cols[1]:
        st.write(st.session_state.lm["analysis.single_setting_analysis.remarked_experiment_img_title"])
        st.write(st.session_state.lm["analysis.single_setting_analysis.remarked_experiment_img_notice"])
        if remarked_list:
            show_images(db, task, remarked_list)
        else:
            st.write(st.session_state.lm["analysis.single_setting_analysis.remarked_experiment_not_found"])
    st.write('---')
    st.markdown(st.session_state.lm["analysis.single_setting_analysis.delete_all_cur_setting_title"])
    st.markdown(st.session_state.lm["analysis.single_setting_analysis.delete_all_cur_setting_warn"])
    if st.checkbox(st.session_state.lm["analysis.single_setting_analysis.delete_all_cur_setting_checkbox"], value=False):
        if st.button(st.session_state.lm["analysis.single_setting_analysis.delete_all_cur_setting_confirm_button"], key='delete_same_setting'):
            delete_all_same_setting_experiment(db, task, same_setting_ids)

def multi_setting_analysis(db):
    st.sidebar.write(st.session_state.lm["analysis.multi_setting_analysis.sidebar_cur_task_title"], st.session_state.cur_analysis_task)
    if st.sidebar.button(st.session_state.lm["analysis.multi_setting_analysis.sidebar_clear_all_recorded_settins_button"], key='clear_recorded'):
        st.session_state.recorded_analysis_setting = []
        st.rerun()
    st.sidebar.write(st.session_state.lm["analysis.multi_setting_analysis.sidebar_recorded_setting_title"])
    st.sidebar.write(st.session_state.lm["analysis.multi_setting_analysis.sidebar_recorded_setting_text"])
    st.sidebar.write(st.session_state.lm["analysis.multi_setting_analysis.sidebar_recorded_setting_notice"])
    # for setting in st.session_state.recorded_analysis_setting:
    #     if st.sidebar.checkbox(f'{setting[0]}-{method_id2remark_name(db, setting[0], setting[1])}-{setting[2]}-{data_id2remark_name(db, setting[2], setting[3])}'):
    #         selected_settings.append(setting)
    options = [f'{setting[0]}~{method_id2remark_name(db, setting[0], setting[1])}~{setting[2]}~{data_id2remark_name(db, setting[2], setting[3])}' for setting in st.session_state.recorded_analysis_setting]                              
    st.session_state.selected_settings = st.sidebar.multiselect(st.session_state.lm["analysis.multi_setting_analysis.sidebar_recorded_setting_select"], options, default=options)
    selected_settings = [setting.split('~') for setting in st.session_state.selected_settings]
    # st.write(selected_settings)
    result_table = db[f'result_{st.session_state.cur_analysis_task}']
    metrics = [col for col in result_table.columns if not col.startswith("image_") and not col=="experiment_id"]
    selected_metric =  st.sidebar.selectbox(st.session_state.lm["analysis.multi_setting_analysis.sidebar_metric_select"], metrics)
    if len(selected_settings) > 0:
        st.write(st.session_state.lm["analysis.multi_setting_analysis.statistics_results_title"].format(SELECTED_METRIC=selected_metric))
        df_list = []
        num_records_list = []
        for setting in selected_settings:
            result_statistics, same_ids = get_result_statistics(db, st.session_state.cur_analysis_task, setting[0], method_remark_name2id(db, setting[0], setting[1]), setting[2], data_id2remark_name(db, setting[2], setting[3]))
            if result_statistics is not None:
                df_list.append(result_statistics[selected_metric])
                num_records_list.append(len(same_ids))
        if len(df_list) > 0:
            df = pd.concat(df_list, axis=1)
            df.loc['Counts'] = num_records_list

            df.columns = [f'{setting[0]}-{method_id2remark_name(db, setting[0], setting[1])}-{setting[2]}-{data_id2remark_name(db, setting[2], setting[3])}' for setting in selected_settings]
            st.dataframe(df, use_container_width=True) 
        st.write(st.session_state.lm["analysis.multi_setting_analysis.statistics_score_metrics_title"].format(SELECTED_METRIC=selected_metric))
        plot_type = st.selectbox(st.session_state.lm["analysis.multi_setting_analysis.statistics_chart_type_select"], ['Boxplot', 'Violinplot', 'Lineplot', 'Barplot'], index=0)
        multi_setting_plot(db, st.session_state.cur_analysis_task, selected_settings, selected_metric, plot_type)
    else:
        st.write(st.session_state.lm["analysis.multi_setting_analysis.no_setting_selected_text"])
    # st.sidebar.write(selected_settings)
    
def sidebar_select_analysis():
    st.sidebar.markdown(st.session_state.lm["analysis.sidebar_select_analysis.title"])
    return st.sidebar.radio(st.session_state.lm["analysis.sidebar_select_analysis.radio_text"],
                            [
                                st.session_state.lm["analysis.sidebar_select_analysis.radio_choice1"],
                                st.session_state.lm["analysis.sidebar_select_analysis.radio_choice2"],
                            ])
        
def select_setting(db):
    st.write(st.session_state.lm["analysis.select_setting.title"])
    cols = st.columns(3)
    with cols[0]:
        st.write(st.session_state.lm["analysis.select_setting.select_task_title"])
        task_sql = f'SELECT DISTINCT task FROM experiment_list'
        tasks = [t[0] for t in db.conn.execute(task_sql).fetchall()]
        task = st.selectbox(st.session_state.lm["analysis.select_setting.select_task_select"], tasks)
                
    with cols[1]:
        st.write(st.session_state.lm["analysis.select_setting.select_method_title"])
        method_sql = f'SELECT DISTINCT method FROM experiment_list WHERE task="{task}"'
        methods = [m[0] for m in db.cursor.execute(method_sql).fetchall()]
        method = st.selectbox(st.session_state.lm["analysis.select_setting.select_method_select"], methods)
        
    with cols[2]:
        st.write(st.session_state.lm["analysis.select_setting.select_data_title"])
        dataset_sql = f'SELECT DISTINCT data FROM experiment_list WHERE task = "{task}" AND method = "{method}"'
        datasets = [d[0] for d in db.conn.execute(dataset_sql).fetchall()]
        dataset = st.selectbox(st.session_state.lm["analysis.select_setting.select_data_select"], datasets)
        
    with cols[1]:
        method_id_sql = f'SELECT DISTINCT experiment_list.method_id, method_{method}.remark FROM \
            experiment_list INNER JOIN method_{method} ON experiment_list.method_id = method_{method}.method_id \
            WHERE task = "{task}" AND method = "{method}" AND data = "{dataset}"'
        method_ids = {(m[1] if m[1] is not None else m[0]):m[0] for m in db.conn.execute(method_id_sql).fetchall()}
        method_id = st.selectbox(st.session_state.lm["analysis.select_setting.method_id_select"], method_ids.keys())
        method_id = method_ids[method_id]
        if method_id != -1:
            method_table = db[f'method_{method}']
            method_info = method_table.select(where=f'method_id={method_id}')
            method_columns = method_table.columns
            method_info = pd.DataFrame(method_info, columns=method_columns)
            # method_remark_name = method_info['remark'][0]
            method_info = method_info.drop(columns=['method_id', 'remark'])
            method_info.index = [st.session_state.lm["analysis.select_setting.method_index"]]
            # if method_remark_name:
            #     st.write(f'_Remark Name_: **{method_remark_name}**')
            st.dataframe(method_info.astype(str).transpose(), use_container_width=True, height=150)
            if st.checkbox(st.session_state.lm["analysis.select_setting.remark_method_checkbox"], key='remark_method'):
                remark = st.text_input(st.session_state.lm["analysis.select_setting.remark_method_input"], key='remark_input')
                if remark.isnumeric():
                    st.session_state.error_flag1 = True
                if remark == '':
                    remark = None
                if st.button(st.session_state.lm["analysis.select_setting.remark_method_button"], key='confirm_remark_method'):
                    try:
                        method_table.update(where=f'method_id={method_id}', remark=remark)
                        db.conn.commit()
                    except:
                        st.session_state.error_flag = True
                    st.rerun()
                if st.session_state.error_flag:
                    st.write(st.session_state.lm["analysis.select_setting.remark_method_failed_repeat"])
                    st.session_state.error_flag = False
                if st.session_state.error_flag1:
                    st.write(st.session_state.lm["analysis.select_setting.remark_method_failed_number"])
                    st.session_state.error_flag1 = False
        else:
            st.write(st.session_state.lm["analysis.select_setting.method_no_param"])
        
        
    with cols[2]:
        dataset_id_sql = f'SELECT DISTINCT data_id FROM experiment_list WHERE task = "{task}" AND method = "{method}" AND method_id = "{method_id}" AND data = "{dataset}"'
        dataset_ids = {data_id2remark_name(db, dataset, d[0]):d[0] for d in db.conn.execute(dataset_id_sql).fetchall()}
        dataset_id = st.selectbox(st.session_state.lm["analysis.select_setting.data_id_select"], dataset_ids.keys())
        dataset_id = dataset_ids[dataset_id]
        if dataset_id != -1:
            data_table = db[f'data_{dataset}']
            data_info = data_table.select(where=f'data_id={dataset_id}')
            data_columns = data_table.columns
            data_info = pd.DataFrame(data_info, columns=data_columns)
            # data_remark_name = data_info['remark'][0]
            data_info = data_info.drop(columns=['data_id', 'remark'])
            data_info.index = [st.session_state.lm["analysis.select_setting.data_index"]]
            # if data_remark_name:
            #     st.write(f'_Remark Name_: **{data_remark_name}**')
            st.dataframe(data_info.astype(str).transpose(), use_container_width=True, height=150)
            
            if st.checkbox(st.session_state.lm["analysis.select_setting.remark_data_checkbox"], key='remark_data'):
                remark = st.text_input(st.session_state.lm["analysis.select_setting.remark_data_input"], key='remark_input')
                if remark.isnumeric():
                    st.session_state.error_flag1 = True
                if remark == '':
                    remark = None
                if st.button(st.session_state.lm["analysis.select_setting.remark_data_button"], key='confirm_remark_data'):
                    try:
                        data_table.update(where=f'data_id={dataset_id}', remark=remark)
                        db.conn.commit()
                    except:
                        st.session_state.error_flag = True
                    st.rerun()
                if st.session_state.error_flag:
                    st.write(st.session_state.lm["analysis.select_setting.remark_data_failed_repeat"])
                    st.session_state.error_flag = False
                if st.session_state.error_flag1:
                    st.write(st.session_state.lm["analysis.select_setting.remark_data_failed_number"])
                    st.session_state.error_flag1 = False
        else:
            st.write(st.session_state.lm["analysis.select_setting.data_no_param"])
            
    with cols[0]:
        same_setting_id_sql = f"SELECT id FROM experiment_list WHERE method='{method}' AND method_id={method_id} AND data='{dataset}' AND data_id={dataset_id} AND task='{task}' AND status='finished'"
        if st.checkbox(st.session_state.lm["analysis.select_setting.remark_max_score_checkbox"], key='remark_max_experiment'):
            score_columns = [col for col in db[f'result_{task}'].columns if not col.startswith("image_") and not col=="experiment_id"]
            score_column = st.selectbox(st.session_state.lm["analysis.select_setting.remark_max_score_select"], score_columns, key='score_column_max')
            if st.button(st.session_state.lm["analysis.select_setting.remark_max_score_all_button"], key='confirm_remark_max_all'):
                auto_remark_all_settings_for_task(db, task, score_column, 'max')
                st.rerun()
            if st.button(st.session_state.lm["analysis.select_setting.remark_max_score_cur_button"], key='confirm_remark_max_current'):
                auto_remark_single_setting(db, task, method, method_id, dataset, dataset_id, same_setting_id_sql, score_column, 'max')
                st.rerun()
                
        if st.checkbox(st.session_state.lm["analysis.select_setting.remark_min_score_checkbox"], key='remark_min_experiment'):
            score_columns = [col for col in db[f'result_{task}'].columns if not col.startswith("image_") and not col=="experiment_id"]
            score_column = st.selectbox(st.session_state.lm["analysis.select_setting.remark_min_score_select"], score_columns, key='score_column_min')
            if st.button(st.session_state.lm["analysis.select_setting.remark_min_score_all_button"], key='confirm_remark_min_all'):
                auto_remark_all_settings_for_task(db, task, score_column, 'min')
                st.rerun()
            if st.button(st.session_state.lm["analysis.select_setting.remark_min_score_cur_button"], key='confirm_remark_min_current'):
                auto_remark_single_setting(db, task, method, method_id, dataset, dataset_id, same_setting_id_sql, score_column, 'min')
                st.rerun()
                 
        if st.checkbox(st.session_state.lm["analysis.select_setting.clear_remark_checkbox"], key='clear_remark'):
            st.write(st.session_state.lm["analysis.select_setting.clear_remark_warn"])
            if st.button(st.session_state.lm["analysis.select_setting.clear_remark_all_button"], key='confirm_clear_remark'):
                db[f'experiment_list'].update(where=f'task="{task}"', remark=None)
                db.conn.commit()
                st.rerun()
            if st.button(st.session_state.lm["analysis.select_setting.clear_remark_cur_button"], key='clear_current_remark'):
                db[f'experiment_list'].update(where=f'task="{task}" AND method="{method}" AND method_id={method_id} AND data="{dataset}" AND data_id={dataset_id}', remark=None)
                db.conn.commit()
                st.rerun()
    
    return task, method, method_id, dataset, dataset_id

def show_images(db, task, experiments):
    pattern = re.compile(r'image_(\d+)$')
    image_dict = {}
    selected = st.selectbox(st.session_state.lm["analysis.show_images.experiment_select"], experiments)
    if selected is None:
        st.write(st.session_state.lm["analysis.show_images.experiment_no_remark_text"])
        return
    if selected.isdigit():
        selected_id = int(selected)
    else:
        selected_id = experiment_remark_name2id(db, selected)
    result_info = db[f'result_{task}'].select(where=f'experiment_id={selected_id}')
    result_info = pd.DataFrame(result_info, columns=db[f'result_{task}'].columns)
    
    for name in result_info.columns:
        match = pattern.match(name)
        if match and not result_info[name].isnull().all():
            image_dict[result_info[f"{name}_name"][0]] = result_info[name][0]
        elif result_info[name].isnull().all():
            break
    selected_img = st.selectbox(st.session_state.lm["analysis.show_images.experiment_img_select"], list(image_dict.keys()))
    if selected_img:
        st.image(Image.open(io.BytesIO(image_dict[selected_img])))
        with io.BytesIO(image_dict[selected_img]) as buf:
            img_data = buf.read()
        st.download_button(
            label=st.session_state.lm["analysis.show_images.experiment_img_download_button"].format(SELECTED_IMG=selected_img),
            data=img_data,
            file_name=f"{selected_img}.png",
            mime="image/png"
        )
    else:
        st.write(st.session_state.lm["analysis.show_images.experiment_img_not_exist"].format(SELECTED_ID=selected_id))
        
def delete_all_same_setting_experiment(db, task, same_setting_ids):
    experiment_table = db['experiment_list']
    result_table = db[f'result_{task}']
    for experiment_id in same_setting_ids:
        experiment_table.delete(f'id={experiment_id}')
        result_table.delete(f'experiment_id={experiment_id}')
    db.conn.commit()
    st.session_state.cur_detail_id = None
    st.rerun()

def title():
    st.title(st.session_state.lm["analysis.title"])
    if os.path.exists(st.session_state.db_path) and st.session_state.db_path.endswith('.db'):
        st.write(st.session_state.lm["app.dataset_load_success_text"].format(DB_PATH=st.session_state.db_path))
    else:
        st.write(st.session_state.lm["app.dataset_load_failed_text"])
        
def single_setting_plot(db, task, same_setting_ids, plot_type):
    if plot_type == 'Lineplot' or plot_type == 'Barplot':
        value_type = st.selectbox(st.session_state.lm["analysis.single_setting_plot.value_type_select"], ['Max', 'Min', 'Avg', 'Std', 'Median'], index=2)
    if st.checkbox(st.session_state.lm["analysis.single_setting_plot.customize_checkbox"].format(PLOT_TYPE=plot_type), key='self_defined_plot'):
        cols = st.columns(2)
        with cols[0]:
            figure_size_x = st.number_input(st.session_state.lm["analysis.single_setting_plot.customize_figure_x_input"], value=10, min_value=1, step=1, key='figure_size_x')
        with cols[1]:
            figure_size_y = st.number_input(st.session_state.lm["analysis.single_setting_plot.customize_figure_y_input"], value=6, min_value=1, step=1, key='figure_size_y')
        title = st.text_input(st.session_state.lm["analysis.single_setting_plot.customize_title_input"].format(PLOT_TYPE=plot_type), f'', key='plot_title_single')
        x_label = st.text_input(st.session_state.lm["analysis.single_setting_plot.customize_x_label_input"], f'Metric', key='plot_x_label')
        y_label = st.text_input(st.session_state.lm["analysis.single_setting_plot.customize_y_label_input"], f'Score', key='plot_y_label')
        additional_params_str = st.text_input(st.session_state.lm["analysis.single_setting_plot.customize_additional_param_input"], f'', key='plot_additional_params')
        additional_params_dict = {}
        if not additional_params_str == '':
            additional_params = additional_params_str.split(',')
            for param in additional_params:
                key, value = param.split('=')
                additional_params_dict[key] = value
    else:
        title = ''
        x_label = 'Metric'
        y_label = 'Score'
        figure_size_x = 10
        figure_size_y = 6
        additional_params_dict = {}
    result_table = db[f'result_{task}']
    score_columns = [col for col in result_table.columns if not col.startswith("image_") and not col=="experiment_id"]
    st.sidebar.write(st.session_state.lm["analysis.single_setting_plot.sidebar_metric_select_title"])
    selected_metrics = st.sidebar.multiselect(st.session_state.lm["analysis.single_setting_plot.sidebar_metric_select"], score_columns, default=score_columns)
    if len(selected_metrics) == 0:
        st.write(st.session_state.lm["analysis.single_setting_plot.sidebar_metric_select_empty_text"])
        return
    plot_data = {x_label: [], y_label: []}
    if plot_type == 'Boxplot' or plot_type == 'Violinplot':
        for id in same_setting_ids:
            result = result_table.select(where=f'experiment_id={id}')
            for i, score_column in enumerate(selected_metrics):
                plot_data[x_label].append(score_column)
                plot_data[y_label].append(result[0][i+1])
        plot_df = pd.DataFrame(plot_data)
        if plot_type == 'Boxplot':
            plot_buf = boxplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
        elif plot_type == 'Violinplot':
            plot_buf = violinplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
    elif plot_type == 'Lineplot' or plot_type == 'Barplot':
        result_info = get_result_statistics_by_ids(db, task, same_setting_ids)
        result_info = result_info[selected_metrics]
        plot_data = {x_label: [], y_label: []}
        for i, score_column in enumerate(result_info.columns):
            plot_data[x_label].append(score_column)
            plot_data[y_label].append(result_info.loc[value_type][i])
        plot_df = pd.DataFrame(plot_data)
        if plot_type == 'Lineplot':
            plot_buf = lineplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
        elif plot_type == 'Barplot':
            plot_buf = barplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
    else:
        raise ValueError('Invalid plot type.')
    
    st.image(Image.open(plot_buf))
    plot_buf.seek(0)
    img_data = plot_buf.read()
    plot_buf.close()
    setting = db['experiment_list'].select('method', 'method_id', 'data', 'data_id', where=f'id={same_setting_ids[0]}')[0]
    setting_name = f'{setting[0]}~{method_id2remark_name(db, setting[0], setting[1])}~{setting[2]}~{data_id2remark_name(db, setting[2], setting[3])}'
    st.download_button(
        label=st.session_state.lm["analysis.single_setting_plot.figure_download_button"].format(PLOT_TYPE=plot_type),
        data=img_data,
        file_name=f"{plot_type}_{task if title == '' else title}_{setting_name}.png",
        mime="image/png"
    )
    
def multi_setting_plot(db, task, selected_settings, selected_metric, plot_type):
    if plot_type == 'Lineplot' or plot_type == 'Barplot':
        value_type = st.selectbox(st.session_state.lm["analysis.multi_setting_plot.value_type_select"], ['Max', 'Min', 'Avg', 'Std', 'Median'], index=2)
    if st.checkbox(st.session_state.lm["analysis.multi_setting_plot.customize_checkbox"].format(PLOT_TYPE=plot_type), key='self_defined_plot'):
        cols = st.columns(2)
        with cols[0]:
            figure_size_x = st.number_input(st.session_state.lm["analysis.multi_setting_plot.customize_figure_x_input"], value=10, min_value=1, step=1, key='figure_size_x')
        with cols[1]:
            figure_size_y = st.number_input(st.session_state.lm["analysis.multi_setting_plot.customize_figure_y_input"], value=6, min_value=1, step=1, key='figure_size_y')
        title = st.text_input(st.session_state.lm["analysis.multi_setting_plot.customize_title_input"].format(PLOT_TYPE=plot_type), f'', key='plot_title_multi')
        x_label = st.text_input(st.session_state.lm["analysis.multi_setting_plot.customize_x_label_input"], f'Setting', key='plot_x_label')
        y_label = st.text_input(st.session_state.lm["analysis.multi_setting_plot.customize_y_label_input"], selected_metric, key='plot_y_label')
        col_name_list = st.text_input(st.session_state.lm["analysis.multi_setting_plot.customize_col_name_input"], f'', key='plot_col_name')
        additional_params_str = st.text_input(st.session_state.lm["analysis.multi_setting_plot.customize_additional_param_input"], f'', key='plot_additional_params')
        additional_params_dict = {}
        if not additional_params_str == '':
            additional_params = additional_params_str.split(',')
            for param in additional_params:
                key, value = param.split('=')
                additional_params_dict[key] = value
        if not col_name_list == '':
            col_names = col_name_list.split(',')
            if not len(col_names) == len(selected_settings):
                st.write(st.session_state.lm["analysis.multi_setting_plot.customize_col_name_mismatch_text"])
                return
    else:
        title = ''
        x_label = 'Setting'
        y_label = selected_metric
        col_name_list = ''
        figure_size_x = 10
        figure_size_y = 6
        additional_params_dict = {}
        
    result_table = db[f'result_{task}']
    plot_data = {x_label: [], y_label: []}
    setting_name_dict = {}
    used_setting_names_counts = {}
    for i, setting in enumerate(selected_settings):
        _, same_ids = get_result_statistics(db, task, setting[0], method_remark_name2id(db, setting[0], setting[1]), setting[2], data_remark_name2id(db, setting[2], setting[3]))
        if not col_name_list == '':
            plot_data[x_label].append(col_names[i])
        else:
            str_setting = f'{setting[0]}~{method_id2remark_name(db, setting[0], setting[1])}~{setting[2]}~{data_id2remark_name(db, setting[2], setting[3])}'
            if setting[0] not in used_setting_names_counts :
                setting_name_dict[str_setting] = setting[0]
                used_setting_names_counts[setting[0]] = 1
            elif setting[0] in used_setting_names_counts and str_setting not in setting_name_dict:
                setting_name_dict[str_setting] = f'{setting[0]}_{used_setting_names_counts[setting[0]]}'
                used_setting_names_counts[setting[0]] += 1
        if plot_type == 'Boxplot' or plot_type == 'Violinplot':
            for id in same_ids:
                result = result_table.select(selected_metric, where=f'experiment_id={id}')[0][0]
                plot_data[x_label].append(setting_name_dict[str_setting])
                plot_data[y_label].append(result)
        elif plot_type == 'Lineplot' or plot_type == 'Barplot':
            result_info = get_result_statistics_by_ids(db, task, same_ids)
            result = result_info.loc[value_type][selected_metric]
            plot_data[x_label].append(setting_name_dict[str_setting])
            plot_data[y_label].append(result)
    
    
    plot_df = pd.DataFrame(plot_data)
    for setting_name in plot_df[x_label]:
        if setting_name in used_setting_names_counts and used_setting_names_counts[setting_name] > 1:
            plot_df[x_label] = plot_df[x_label].replace(setting_name, f'{setting_name}_0')
    if plot_type == "Boxplot":
        boxplot_buf = boxplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
    elif plot_type == "Violinplot":
        boxplot_buf = violinplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
    elif plot_type == "Lineplot":
        boxplot_buf = lineplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict)
    elif plot_type == "Barplot":
        boxplot_buf = barplot(plot_df, x_label, y_label, title, (figure_size_x, figure_size_y), **additional_params_dict) 
    else:
        raise ValueError('Invalid plot type.')
    st.image(Image.open(boxplot_buf))
    boxplot_buf.seek(0)
    img_data = boxplot_buf.read()
    boxplot_buf.close()
    st.download_button(
        label=st.session_state.lm["analysis.multi_setting_plot.figure_download_button"].format(PLOT_TYPE=plot_type),
        data=img_data,
        file_name=f"{plot_type}_{task if title == '' else title}_{selected_metric}.png",
        mime="image/png"
    )
            
def auto_remark_all_settings_for_task(db, task, score_column, type_flag:typing.Literal[f'max', f'min']='max'):
    all_setting_sql = f"SELECT DISTINCT method, method_id, data, data_id FROM experiment_list WHERE task='{task}'"
    all_settings = db.conn.execute(all_setting_sql).fetchall()
    for setting in all_settings:
        method, method_id, dataset, dataset_id = setting
        auto_remark_single_setting(db, task, method, method_id, dataset, dataset_id, score_column, type_flag)
        
def auto_remark_single_setting(db, task, method, method_id, dataset, dataset_id, score_column, type_flag:typing.Literal[f'max', f'min']='max'):
    same_setting_id_sql = f"SELECT id FROM experiment_list WHERE method='{method}' AND method_id={method_id} AND data='{dataset}' AND data_id={dataset_id} AND task='{task}' AND status='finished'"
    if  type_flag == 'max':
        score_sql = f"SELECT experiment_id FROM result_{task} WHERE {score_column} = (SELECT MAX({score_column}) FROM result_{task} where experiment_id IN ({same_setting_id_sql})) AND experiment_id IN ({same_setting_id_sql})"
    elif type_flag == 'min':
        score_sql = f"SELECT experiment_id FROM result_{task} WHERE {score_column} = (SELECT MIN({score_column}) FROM result_{task} where experiment_id IN ({same_setting_id_sql})) AND experiment_id IN ({same_setting_id_sql})"
    else:
        raise ValueError('type_flag should be either "max" or "min".')
    score_experiment = db.conn.execute(score_sql).fetchall()
    # st.write(max_score_experiment)
    if len(score_experiment) >= 1:
        score_experiment_id = score_experiment[0][0]
        former_remark = db[f'experiment_list'].select('remark', where=f'id={score_experiment_id}')[0][0]
        if former_remark is None:
            if type_flag == 'max':
                remark=f'{task}_{method}_{method_id2remark_name(db, method, method_id)}_{dataset}_{data_id2remark_name(db, dataset, dataset_id)}_{score_column}_max'
            elif type_flag == 'min':
                remark=f'{task}_{method}_{method_id2remark_name(db, method, method_id)}_{dataset}_{data_id2remark_name(db, dataset, dataset_id)}_{score_column}_min'
            db['experiment_list'].update(remark=None, where=f'remark="{remark}"')
            db[f'experiment_list'].update(where=f'id={score_experiment_id}', remark=remark)
        elif f'{score_column}_max' in former_remark or f'{score_column}_min' in former_remark:
            pass
        else:
            db[f'experiment_list'].update(where=f'id={score_experiment_id}', 
                                            remark=f'{former_remark}_{score_column}_max')
        db.conn.commit()
    else:
        st.write(st.session_state.lm["analysis.select_setting.auto_remark_single_setting_failed_text"])