#!/usr/bin/env python
# coding=utf-8

# Author      :   Xionghui Chen
# Created     :   2017.1.22
# Modified    :   2017.1.23
# Version     :   1.0
# Handler.py
import json
from Route import Route
import random
from functions import multi_probility_test, accumulator, do_probability_test
from Global import cars_info, MAX_PATH
from Car import NoAutoCar
import logging

class CellularHandler(object):

	def __init__(self,fp, car_ratio):
		self.route_list = {}
		self.result_dict = {}
		self.time_slice = 1
		self.car_acc_probility = accumulator(car_ratio)
		self._resource_filter(fp)
		self._route_creator()
		self.car_id_count = 2
		self.remain_rate = 1

	def _route_creator(self):
		"""
			构造线路列表
		"""
		for key,item in self.result_dict.items():
			self.route_list[key] = Route(key,item,self.time_slice)


	def _resource_filter(self,fp):
		"""
			提取原始数据中有用的数据
		"""
		#获取行数
		nrows = fp.nrows
		for i in range(1,nrows):
		    row_data = fp.row_values(i)
		    if self.result_dict.has_key(row_data[0]):
		    	# 不是第一个数据
		    	self.result_dict[row_data[0]].append(row_data[1:])
		    else:
		    	# 是第一个数据
		    	self.result_dict[row_data[0]] = [row_data[1:]]

	def next_car_id(self):
		"""
			新增的car的id
		"""
		new_id = self.car_id_count
		self.car_id_count = self.car_id_count+1
		return new_id

	def car_creator(self,this_road,last_road,output_cars, direction):
		"""
			车辆生产器，用来在道路的开头生产车辆
			需要使用numpy库模拟二项分布
				如果上一个道路段的 车辆个数比这个道路段的少，
					那么新增的车子数目按照二项分布进行生产车子，
					将上一个车道的数目按照留存的比例增加到目前的车道
					进行安排放置
				如果上一个车道的车辆个数比这个车道的多，
					那么这个车道本身不产生新的车子，
					上一个车道的车子按照缺少的比例流失

		"""
		car_dictory = {}
		if last_road == 0:
			# 第一个车道，不需要进行这个操作
			bi_probality = this_road.get_Singleton_peak(0)
			car_amount = multi_probility_test(bi_probality)
			count = 0
			# 本次随机实验计算得应该产生car_amount 量车子
			# print "new car amount is :%s"%car_amount
			while(count < car_amount):
				# 产生对应类型的汽车
				car_type = multi_probility_test(self.car_acc_probility)
				single_car_info = cars_info[car_type]
				max_vel = single_car_info['max_velocity']
				# [todo] 正太分布
				init_vel = random.randint(2, max_vel/3)
				# print "[car_creator]new car type is %s"%single_car_info['type']
				if single_car_info['type']==0:
					# 自动驾驶汽车
					pass
				else:
					new_car = NoAutoCar(init_vel, single_car_info)
					car_id = self.next_car_id()
					car_dictory[car_id] = new_car
					print "new car id is :%s"%car_id
					logging.info("new car id is :%s"%car_id)
				count = count + 1
		#[todo] 合并新老车
		#[todo] 新车生成
		elif last_road.car_volume() < this_road.car_volume():
			# 将上一个路段的车子按照比例增加在该路段
			output_amount = len(output_cars)
			for key,value in output_cars.items():
				print "[create car ] self.remain_rate%s"%self.remain_rate
				if do_probability_test(self.remain_rate):
					# 以增加的比例为概率，判断该量车是否进入这一个车道
					car_dictory[key] = value
				else:
					pass
					# 舍弃该车
			# 上一个道路段的车辆个数比这个道路段少，按比例产生新的车子
			bi_probality = this_road.get_Singleton_peak(last_road.car_volume())
			car_amount = multi_probility_test(bi_probality)
			count = 0
			while(count < car_amount):
				# 产生对应类型的汽车
				car_type = multi_probility_test(self.car_acc_probility)
				single_car_info = cars_info[car_type]
				max_vel = single_car_info['max_velocity']
				init_vel = random.randint(0, max_vel)
				if single_car_info['type']==0:
					# 自动驾驶汽车
					pass
				else:
					new_car = NoAutoCar(init_vel, single_car_info)
					car_id = self.next_car_id()
					car_dictory[car_id] = new_car
				count =count + 1
		else:
			for key,value in output_cars.items():
				print "[create car ] self.remain_rate%s"%self.remain_rate
				if do_probability_test(self.remain_rate):
					# 以增加的比例为概率，判断该量车是否进入这一个车道
					car_dictory[key] = value
				else:
					pass
		return car_dictory

	def driver(self,route_id):
		"""
			元胞驱动器，用来启动所有程序流程
		"""
		count = 0 
		while count < 100:
			self.itertor(self.route_list[route_id],'up')
			count = count + 1
			print "driver count is :%s"%count
		logging.info(self.route_list[route_id].road_list[0].inc_path.recorder)
		self.route_list[route_id].plot(self.car_id_count)

	def itertor(self, route, direction):
		"""
			迭代控制器,控制每次迭代进行的更新操作
			- 从头开始更新路段信息，
			- 将一个路段更新的结果传递给下一个路段
			- 进行道路车辆的道路选择
			- 记录本次更新的结果，用于最后绘图
			- 对下一个路段进行更新，
			- 一直到路段更新结束
		"""
		last_road = 0
		#[todo] 将上个车道的output加入这个车道的input
		output_cars = 0
		for index, road in enumerate(route.road_list):
			if index < len(route.road_list) - 1:
				# 设置保留率，如果从不拥堵的路段过渡到拥堵的路段，则有保留率，否则，保留率为1
				next_road = route.road_list[index+1]
				rate = (road.car_volume()/next_road.car_volume())

				if rate >1:
					self.remain_rate =  (next_road.car_volume()/road.car_volume())
				else:
					self.remain_rate = rate
			car_dictory = self.car_creator(road,last_road,output_cars,direction)
			output_cars = self.update(road,car_dictory,direction)
			last_road = road

	def update(self,road, car_dictory,direction):
		"""
			操作一个道路路段的更新
			1. 按照概率分布和上一个路段对本路段的影响创造汽车
			2. 对每辆汽车进行元胞迭代操作
				- 变道判断[自动车解决冲突]
				- 前进更新
			3. 将更新结果更新到地图中
			4. 返回更新结果
		"""
		if direction =='up':
			path = road.inc_path
			logging.info("[handler.update]update car_dictory is :%s"%car_dictory)
			for car_id,car in car_dictory.items():
				# car.change_lanes()
				path.add_car(car,car_id)
			output_cars = path.update(self.remain_rate)
			# logging.info("completed update:%s"%path.recorder[MAX_PATH - 1][-1])
		return output_cars

	def path_log_recorder(self,path):
		"""
			记录这个过程的每次状态信息，用于绘图
		"""

	def get_single_lines_cars(self,car):
		location = car.get_place()
		lanes = car.get_lanes()