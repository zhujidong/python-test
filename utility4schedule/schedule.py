# -*- coding:utf_8 -*-

'''
The MIT License (MIT) 
zhujidong 2021 Copyright(c), WITHOUT WARRANTY OF ANY KIND.

'''


import time
from threading import Timer


class Schedule(object):
    '''
    管理计划任务；每个任务以线程方式运行。
    
    主要方法：
    reg_thread（），注册一个任务，即可按计划运行此任务。
    list_threads(),列出已经注册的任务名称和计划表
    close_threads(),关闭所有线程，退出主程序时调用此方法。
    pause_thread()，按名字暂停某个任务。
    restart_thread()，恢复某个任务的执行 //未完成
    '''

    def __init__(self) -> None:

        self.threads = {}
        '''
        记录reg_thread（）时所有计划任务线程的信息，key为给任务起的“名字”，value为线程信息。
        value仍是一个字典，其key值含义如下：
            fun:str,要注册的任务线程的方法函数
            param:tuple,任务线程的参数，**只能传递位置参数给fun **
            schedule:str,任务执行的计划，计划的定义方式见config.ini和 ConfigReader.getschedule()方法
            retry:tuple(int,int)，线程执行失败时，重试次数与时间间隔（默认重试1次，隔360秒后重试）
            errors:int,记录线程执行失败次数
            handle:线程的句柄，供取消等使用
        '''

    def reg_thread( self, name:str, fun:object, param:tuple, 
                    schedule:str, retry:tuple=(1,360),run_now:bool=False) -> None:
        '''
        将一个方法函数，注册为一个计划任务
        *要求此方法函数返回一个逻辑值，真代表成功，假代表任务失败。
        *只能传给任务函数位置参数

        :param:
            name:str,为计划任务的起的名称
            run_now:bool,注册计划任务后是否立即执行一次，再按按计划执行
            其它参数相关信息，见__init__()。
        '''
        thread = {'fun':fun, 'param':param, 'schedule':schedule, 'retry':retry, 'errors':0, 'handle':None}
        self.threads[name] = thread
        self._run_thread(name, run_now)
        return None


    def _run_thread(self, name, run_now=True) -> None:
        '''
        调用Timer启动线程，每个线程就是一个等待下次计划时间运行的任务

        :param:
            name:str,要执行的任务名称
            run_now:bool,为真时，立即运行任务而不管计划，然后设置下次计划时间运行
                         为假时，读取计划，设置计划时间运行。
                    *当此方法按计划调用自身时，通常为真，因为是到了计划时间才调用的，当然要运行任务
                    *通常是给注册任务时使用，看是否当即运行一次，还是按计划时间运行
        '''
        
        #立即运行任务而不管计划，然后求出下次计划时间
        if run_now:
            now = time.strftime("%m月%d日%H:%M", time.localtime(time.time()))
            print(F'\r\n----------------------------\r\n{now}：”{name}“任务启动...')
            
            #运行计划的任务，成功返回真。      *此处只将元组展开成位置参数给要执行的方法*
            rs = self.threads[name]['fun'](*self.threads[name]['param'])
                        
            #调用方法生成到下次的执行任务的间隔秒数
            interval, nextdatetime = Schedule._get_interval(self.threads[name]['schedule'])
            nextdatetime = time.strftime("%m月%d日%H:%M", nextdatetime)

            #根据任务执行的返回结果，调整下次执行间隔和提示信息
            if rs:
                self.threads[name]['errors'] = 0
                info = F'“{name}”任务执行完毕，下次计划于{nextdatetime}启动'
            #任务执行中失败
            else:
                self.threads[name]['errors'] += 1
                #没达到重试次数，调整下次执行的间隔为重试间隔
                if self.threads[name]['errors']  <= self.threads[name]['retry'][0]:
                    interval = self.threads[name]['retry'][1]
                    info = F'”{name}“任务执行失败，将在{interval/60}分种后重启...'
                else:
                    info = F'”{name}“任务已失败{self.threads[name]["errors"]}次，不再重试，将在下次计划时间（{nextdatetime}）启动。'
                    self.threads[name]['errors'] = 0
        #非立即运行的任务，调用得到时间间隔即可
        else:
            interval, nextdatetime = Schedule._get_interval(self.threads[name]['schedule'])
            nextdatetime = time.strftime("%m月%d日%H:%M", nextdatetime)
            info = F'“{name}”任务将按计划将于{nextdatetime}运行。'

        #使用Timer,设置在计划时间段后，以线程方式运行本方法
        print(info,'\r\n----------------------------\r\n')
        self.threads[name]['handle'] = Timer(interval, self._run_thread, args=(name, True))
                                       #计划时间后才运行，所以通常给本方法传递true以立即运行任务
        self.threads[name]['handle'].start()
        return None


    def pause_thread(self, name) -> str:
        '''
        暂停某个计划的任务
        '''
        info = 0
        if name in self.threads.keys():
            self.threads[name]['handle'].cancel()
            info = F'"{name}"任务已暂停。'
        else:
            info = F'"{name}"任务不存在。'
        return info

    def restart_thread(self, name) -> None:
        '''
        重启某个计划的任务
        '''
        info = 0
        if name in self.threads.keys():
            self._run_thread(name, run_now=False)
            info = F'"{name}"任务重启完成。'
        else:
            info = F'"{name}"任务不存在。'
        return info


    def run_thread(self, name) -> str:
        '''
        立即运行一次某个已注册的任务
        '''
        info = 0
        if name in self.threads.keys():
            self._run_thread(name, run_now=True)
            info = F'"{name}"立即运行任务完成。'
        else:
            info = F'"{name}"任务不存在。'
        return info


    def list_threads(self) -> None:
        #for key, values in self
        return None


    def close_threads(self) -> None:
        '''
        取消所有线程，退出程序前调用
        '''
        for thread in self.threads.values():
            if thread['handle']:
                thread['handle'].cancel()
        return None


    @staticmethod
    def _get_interval(schedule:list[tuple]) -> tuple:
        """
        根据计划schedule（元组列表），计算现在到下次计划间隔的秒数。
        
        :param:
            schedule：执行任务的计划表，是两个元素的元组列表。如
                [ ('6,7', '09:00, 14:00, 17:00'), 
                  ('1,5', '08:30, 10:30, 13:30, 15:30, 17:30, 20:00'), 
                  ('3', '3600, 06:00, 22:00') ]
                具体实现的功能和含义见下面config.ini文件中样式说明，
                用ConfigParser实例的items(“my_schedule”)方法读出即是上面schedule格式
                                
                （config.ini文件格式）
                # -*- coding:utf_8 -*-
                [my_schedule]
                #一星期内每天配置不同的计划方式，按星期循环
                #等号左边代表星期几，1代表星期一，7代表星期日，星期几若重复，后面会覆盖前面的设置

                #定点执行：要求HH:MM格式，且从小到大排序
                6,7 = 09:00, 14:00, 17:00
                1,5 = 08:30, 10:30, 13:30, 15:30, 17:30, 20:00    

                #间隔执行：3600秒执行一次，仅在06:00——22:00之间执行
                3 = 3600, 06:00, 22:00
                
        :return: 
            至下次计划的间隔秒数, 下次计划的日期时间
        """
        
        #整理成按星期排序的计划列表
        temp ={}
        for sche in schedule:
            #转换成以星期几为键的字典，以消除重复的计划
            week = sche[0].replace(' ', '').split(',')
            table = sche[1].replace(' ', '').split(',')
            for w in week:
                temp[int(w)] = table
        schedule = sorted(temp.items(),key=lambda x:x[0])
        #print("整理后的格式为：", schedule)
        '''
            [ (1, ['08:30', '10:30', '13:30', '15:30', '17:30', '20:00']), 
              (3, ['3600', '06:00', '22:00']), 
              (5, ['08:30', '10:30', '13:30', '15:30', '17:30', '20:00']), 
              (6, ['09:00', '14:00', '17:00']), 
              (7, ['09:00', '14:00', '17:00']) ]
        '''

        #获取当前时间戳，星期几，日期，时间
        stamp = time.time()
        struct = time.localtime(stamp)
        day_of_week = struct[6] + 1 # 1,周一；7，周日        
        date_ = time.strftime("%Y-%m-%d", struct)
        time_ = time.strftime("%H:%M", struct)

        #提取当天的计划列表 和 下一天任务是星期几和对应计划列表
        table = None
        for sche in schedule:
            if sche[0] == day_of_week:
                table = sche[1]
            elif sche[0] > day_of_week:
                next_day_of_week = sche[0]
                next_table = sche[1]
                break
        else:
            #只有被break，才“不会”执行此处。（一次没执行或顺利执行完循环，都“会”执行此处）
            #没有被break，说明在列表中没有找到“next”的数据 ，则设置为第一个。
            next_day_of_week = schedule[0][0]
            next_table = schedule[0][1]
        
        #先在当天中查找下次计划，找到设置 next_stamp，否则置为 None
        next_stamp = None
        #当天有计划，并且是定点执行的
        if table and ':' in table[0]:
            for tb in table:
                if tb > time_:
                    next_stamp = time.mktime(time.strptime(F'{date_} {tb}', '%Y-%m-%d %H:%M'))  
                    break
        #当天有计划，是按时间间隔执行
        elif table:
            next_stamp = stamp + int(table[0])
            next_time = time.strftime("%H:%M", time.localtime(next_stamp))
            #下个计划没到当天计划开始时间
            if next_time <=  table[1]:
                next_stamp = time.mktime(time.strptime(F'{date_} {table[1]}', '%Y-%m-%d %H:%M'))  
            #超计划的时间段了，不是今天的计划了
            elif next_time >= table[2]:
                next_stamp =None

        #当天没有计划或当天计划的时间之外
        if next_stamp is None:
            #设置计划为下一个天的开始时间就可
            if ':' in next_table[0]:
                next_time = next_table[0]
            else:
                next_time = next_table[1]

            #下个计划天与今天相距的天数
            if next_day_of_week <= day_of_week:
                next_day_of_week += 7
            days = next_day_of_week - day_of_week

            # 用 今日 和 下次计划时间 生成的时间戳，再加上相差天数的的秒数，即为下次计划的时间戳。
            next_stamp = time.mktime(time.strptime(F'{date_} {next_time}', '%Y-%m-%d %H:%M'))  
            next_stamp += days*24*3600

        interval = next_stamp - stamp
        return interval, time.localtime(next_stamp)