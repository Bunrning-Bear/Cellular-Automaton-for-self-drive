#!/usr/bin/env python
# coding=utf-8

# Author      :   Xionghui Chen
# Created     :   2017.1.21
# Modified    :   2017.1.23
# Version     :   1.0
# structure.py
import logging
from functions import do_probability_test
from Global import MAX_PATH
"""
车的基类
"""
class BasicCar(object):
	
	def __init__(self, init_vel,car_info):
		self.velocity=init_vel # 当前行驶速度
		self.max_velocity=car_info['max_velocity']# 车辆的限制速度
		self.length=car_info['length']# 车辆长度
		self.location=[MAX_PATH,0]# 车辆当前的位置，在路段的多个车道内定义:[x,y]
		self.accelerate=1# 车辆的等效加速度
		self.slow_rate = car_info['slow_rate']
		self.slow_rate_low = 0.01
		self.slow_velocity = 1
		self.safe_distance = car_info['safe_distance']
		self.slow_rate_high = 0.75


	def set_location(self,lanes,place):
		"""
			设置车辆的位置
		"""
		self.location[0] = lanes
		self.location[1] = place

	def get_lanes(self):
		"""
			返回该车辆现在所在的车道位置
		"""
		return self.location[0]


	def update_infomation(self, vn):
		"""
			设置新的坐标位置
		"""
		self.velocity = vn
		self.location[1] = self.location[1] + vn

	def get_place(self):
		"""
			返回该辆车现在所在的前进的位置
		"""
		return self.location[1]

	def get_distance(self, another_car):
		"""
			headway = 两辆车的坐标差- 前面的车的长度
		"""
		distance = abs(another_car.location[1] - self.location[1])
		if self.get_place() > another_car.get_place():
			length = self.length
		else:
			length = another_car.length
		return distance - length

	def get_slow_rate(self,vn):
		"""
			获得随机慢化概率
		"""
		if vn == self.max_velocity :
			return self.slow_rate_low
		elif vn ==0:
			return self.slow_rate_high
		else:
			return self.slow_rate

	def do_slow(self,vn):
		return max(vn-self.slow_velocity,0)

	def change_lanes(self, around_cars, has_token, lance_amount):	
		"""
			lance_amount:总的车道的数目
			has_token:已经被占据的格子
			around_cars: include 
				'l+':left_forward_car,
				'l-':left_back_car, 
				'r+':right_forward_car, 
				'r-':right_back_car
			根据左右最近车的位置情况做出车道变道决策
			b. 换车道思考过程：
				i. 三车道换道模型
					1) 如果右车道安全，且比当前车道车况好[车距更大]，就换右车道
					2) 右车道路况没有比当前路况好，那么
						a) 如果左车道安全
						b) 当前车道不满足行驶条件
						c) 左车道路况比当前路况好
						d) 满足以上所有条件，换左车道
					3) 做出最后的换道决策，前面只是做出思考，有Pignore的概率拒绝换道[模拟人的因素]
					4) 这部分私家车和自动驾驶汽车暂时没有思考出区别
				ii. 考虑鸣笛效应
					1) 当n号车后面的车满足以下条件的时候，对n号车鸣笛
						a) n号车无法正常速度行驶
						b) n号车无法换道
					2) 当n号车被鸣笛之后：
						a) 如果右车道安全，且比当前车道车况好，就换右车道
						b) 如果右车道不能换，那么
							i) 如果左车道安全
							ii) 左车道满足当前的行驶条件[速度满足当前的速度]
						c) 决定换左车道
					3) 上面只是做出思考，没有做出最终决策，有Pignore的概率拒绝换道[模拟人的因素]
					4) 换道环节结束之后进入单车道思考过程
		"""
		# 考虑右边车道
		#if self.location[0] - 1 >= MAX_PATH - lance_amount:
		# try:
		# 	right_location = [self.location[0] - 1, self.location[1]]

		# 考虑左边车道
		#if self.location[0] + 1 < MAX_PATH
		# 换道决策
		pass

	def update_status(self, around_cars):
		"""
			around_cars: include 
				forward_cars ：观察两辆
				back_cars
			i. 加速过程：Vn->min(vn+1,vmax)
				1) 私家车和自动驾驶汽车应该有不同的加速度，1应该取值不同，下同
			ii. 减速过程【应用加速效应模型进行改进】：vn->min(vn,,dn+v'n+1)[n号的加速度为1[最大加速度]，和考虑了前车的位移的情况下的两者的间距]
				1) 为了避免相撞
				2) v'n+1=vn+1 - dsafe[安全距离]
				3) 对于自动驾驶汽车而言，安全距离减小，因为他能够灵活反应，对应在元胞机中，自动驾驶汽车是在私家车做出决策之后进行的决策，所以他所看到的私家车的vn是确定化的vn不会产生冲突
			iii. 随机慢化：
				1) 随机慢化的思想：模拟驾驶员状态导致的慢化
				2) 【应用巡航驾驶极限模型和VDR慢启动规则改进】
					a) 思想：
						i) 以期望的速度行驶[vmax]，不受随机慢化影响
						ii) 在上一刻静止的车辆，随机慢化的概率更大
					b) Pc = p(v) ->当v=0和v=max的时候，随机慢化概率远小于1，其他时间段随机慢化较高
					c) 进行随机慢化，在pc的概率下，vn->max(vn-1,0)
				3) 由于自动驾驶汽车的特性，其pc函数的值应该比私家车的低
			iv. 进行运动决策：xn->xn+vn
			v. 注意，这之前的步骤是每个步骤都要走一遍的，直到最后一步完成之后，再更新状态
		"""
		# 加速
		# logging.info("velocity is %s"%self.velocity)
		# logging.info("forward car number is %s"%len(around_cars))
		# logging.info("location is :%s"%self.location)

		vn = min(self.velocity+self.accelerate, self.max_velocity)
		# 减速
		if len(around_cars) == 2:
			v_forward_imaginary = min(
				around_cars[0].max_velocity - self.safe_distance,
				max(around_cars[0].velocity - self.safe_distance,0),
				max(0,around_cars[0].get_distance(around_cars[1]) - self.safe_distance))
		elif len(around_cars) == 1:
			#这辆车前面只有一辆车，第三项消除
			v_forward_imaginary = min(
				max(around_cars[0].max_velocity - self.safe_distance,around_cars[0].length),
				max(around_cars[0].velocity - self.safe_distance,around_cars[0].length),
				999999)
			# logging.info("v forward imaginary is :%s"%v_forward_imaginary)
		if len(around_cars) != 0:
			# logging.info("distance is :%s"%self.get_distance(around_cars[0]))
			vn = min(vn,self.get_distance(around_cars[0])+v_forward_imaginary)
		# logging.info("vn before slow is %s"%vn)	
			# 这辆车前面没有车，不会受限制
		# 随机慢化
		# 计算当前随机漫画概率
		slow_rate = self.get_slow_rate(vn)
		if do_probability_test(slow_rate):
			# 进行随机慢化
			vn = self.do_slow(vn)
		# 更新速度
		# 返回更新后的坐标
		# logging.info("vn after slow is %s"%vn)	
		return (vn, [self.location[0], self.location[1]+vn])


class NoAutoCar(BasicCar):
    def __init__(self, *argc, **argkw):
        super(NoAutoCar, self).__init__(*argc, **argkw)  
