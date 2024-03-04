# pyerm (Python Experiment Record Manager)
This project is an experiment record manager for python based on SQLite DMS, which can help you efficiently save your experiment settings and results for latter analysis. 

*In the current version, all operations will be performed locally.*

# Introduction
This project is used to save the settings and results of any experiment consists of three parts: method, data, task. 

Besides, the basic information and detail information of the experiment will also be recorded.

All data you want can be efficiently saved by API provided without knowing the detail implement, but I suggest reading the table introduction for further dealing with the records. 

## Workflow Introduction
### Table Define & Init
Before starting the experiment, you need to init the tables you need for the experiment by three init function: `data_init()`, `method_init()`, `task_init()`.

 You need to input the name and experiment parameter for the first two. The function can automatically detect the data type, and they will create the table if not exist. If you want to define the DMS type yourself, you can input a `param_def_dict` to these function, whose key means column name, and value means column SQL type define, like `{"people", "TEXT DEFAULT NULL"}`. 

### Experiment 

The experiment recorder mainly consists of four parts, `experiment_start()`, `experiment_over()`, `experiment_failed()`, `detail_update()`. From the name of these function, you can easily know where and how to use them.

`experiment_start()` saves the basic experiment information before experiment formally starts and will set the experiment status to running.

`experiment_over()` saves the experiment results after experiment ends and will set the experiment status to over.

`experiment_failed()` saves the reason why experiment failed and will set the experiment status to failed.

`detail_update()` saves the intermediate results. It's optional, and if you never use it and don't manually set the define dict, the detail table may not be created.

## Table Introduction

### Experiment Table
All experiments' basic information will be recorded in the experiment_list table. It contains the description of the method, the method (with its setting id) & data (with its setting id) & task, the start & end time of the experiment, useful & total time cost, tags, experimenters, failure reason and the experiment status, each experiment is identified by the experiment id.

### Method Table
Each Method Table is identified by its corresponding method name, and any different method will be assigned a different table for saving its different parameter setting, such as method-specific hyper-parameters, etc. The table is used to save different parameter for every method.

The only necessary column for method table is the method setting id, which will be set automatically, other specific column is set by users.

### Data Table
Each Data is identified by its corresponding data name, and any different data will be assigned a different table for saving its different parameter setting, such as data-specific preprocess parameters, etc. The table is used to save different parameter for every data.

The only necessary column for method table is the data setting id, which will be set automatically, other specific column is set by users.

### Result Table
Each Result Table is identified by its corresponding task name, and different tasks will be assigned with different tables for saving its different experiment results, such as accuracy for classification, normalized mutual information for clustering. 

Besides, this table offers several columns for saving image in order for latter visualization. 

The only necessary column for result table is the experiment id, other specific column is set by users.

### Detail Table
Each Detail Table is identified by its corresponding method name, different methods are related to different detail table. During an experiment, you may need to record some intermediate results, which can be saved in this table.

The only necessary column for detail table is the detail id (which can be set automatically) and the experiment id, other specific column is set by users.


# Future Plan

- [ ] Some Scripts For Better Usage 
- [ ] Experiment Summary Report Generate
- [ ] Web UI Visualize & Commonly Used Analyze Fuctions

# Contact
My email is yx_shao@qq.com. If you have any question or advice, please contact me. 
