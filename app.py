import faicons as fa
import plotly.express as px
import plotly.graph_objs as go
import plotly.tools as tls
import pandas as pd
import numpy as np

# Load data and compute static values
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly
import matplotlib.pyplot as plt
import math
import matplotlib.colors as colors
import seaborn as sns

class Patient:
    def __init__(self, path__, file):
        
        self.file_path = path__ + file
        self.data = pd.read_csv(self.file_path, sep=';', encoding='iso-8859-1').set_index('FRONT').iloc[:, :-1].iloc[:140, 2:]
        self.data = (1.3375 - 1) / self.data * 1000
        self.r0 = 3.5
        
        self.x_len, self.y_len = self.data.shape
        self.x_zero_index = self.data.index.tolist().index('0.000')
        self.y_zero_index = self.data.columns.tolist().index('0.000')
        
        self.smooth_data = pd.DataFrame()
        self.smooth(3)
        
        self.min_distance = 0
        self.smooth_data_with_min_for_plot = self.smooth_data.copy()
        self.find_min()
        
        self.df_133std = pd.DataFrame()
        self.area_133std = 0
        self.find_133std_area()
        
        self.df_overlap = self.df_133std.copy()
        self.df_edge = pd.DataFrame()
        self.edge_para_df = pd.DataFrame()
        self.overlap_cal()
        
        self.incircle_diatance = 0
        self.df_incircle = self.smooth_data.copy()
        self.incircle()
        
        self.two_point_mean_max, self.two_point_angle, self.two_point_pend_mean, self.two_point_pend_angle = 0, 0, 0, 0
        self.two_point_zone_mean, self.two_point_pend_zone_mean = 0, 0
        self.two_point_zone_for_plot = self.df_overlap.copy()
        self.find_two_point_max()
        
        self.zone_mean_max, self.zone_angle, self.zone_pend_mean, self.zone_pend_angle = 0, 0, 0, 0
        self.find_zone_max()
        
        self.ring_overlap = self.df_133std.copy()
        self.ring_edge = pd.DataFrame()
        self.ring_para_df = pd.DataFrame()
        self.ring_mean_max, self.ring_angle, self.ring_pend_mean, self.ring_pend_angle = 0, 0, 0, 0
        self.find_ring_max()
        
    def smooth(self, smooth_num):
        v_df = pd.DataFrame(self.data)
        for i in v_df.columns:
            v_df[i] = 0
        r1 = smooth_num / 2
        cpl = self.circle_mat(r1 * 10)
        n = 0
        for shift1, shift2 in cpl:
            v_df += self.data.shift(shift1).shift(shift2, axis=1)
            n += 1
        self.smooth_data = v_df / n
    
    def find_min(self):
        overall_min = self.smooth_data_with_min_for_plot.min().min()
        min_index = self.smooth_data_with_min_for_plot.stack().idxmin()
        self.min_distance = (float(min_index[0]) ** 2 + float(min_index[1]) ** 2) ** 0.5
        self.smooth_min_value = self.smooth_data_with_min_for_plot.loc[min_index[0], min_index[1]]
        min_index = (self.smooth_data_with_min_for_plot.index.tolist().index(min_index[0]),
                     self.smooth_data_with_min_for_plot.columns.tolist().index(min_index[1]))
        self.smooth_data_with_min_for_plot.iloc[min_index[0] - 1, min_index[1] - 1] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0] - 1, min_index[1]] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0] - 1, min_index[1] + 1] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0], min_index[1] - 1] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0], min_index[1]] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0], min_index[1] + 1] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0] + 1, min_index[1] - 1] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0] + 1, min_index[1]] = np.nan
        self.smooth_data_with_min_for_plot.iloc[min_index[0] + 1, min_index[1] + 1] = np.nan
    
    def find_133std_area(self):
        r2 = 8 / 2
        std_list = []
        self.point_list = []
        for k1 in range(self.x_len):
            for k2 in range(self.y_len):
                distance = ((k1 - self.x_zero_index) ** 2 + (k2 - self.y_zero_index) ** 2) ** 0.5 * 0.1
                if distance < r2:
                    std_list += [self.data.iloc[k1, k2]]
        std_ = np.nanstd(std_list)
        self.df_133std = self.smooth_data.copy()
        area = 0
        for i in range(self.x_len):
            for j in range(self.y_len):
                if self.df_133std.iloc[i, j] < self.smooth_min_value + 1.33 * std_:
                    self.df_133std.iloc[i, j] = np.nan
                    area += 0.01
                    self.point_list += [(i, j)]
        self.area_133std = area
    
    def overlap_cal(self):
        for i in range(self.x_len):
            for j in range(self.y_len):
                dis_zero = ((i - self.x_zero_index) ** 2 + (j - self.y_zero_index) ** 2) ** 0.5 * 0.1
                if dis_zero < self.r0 / 2:
                    if np.isnan(self.df_overlap.iloc[i, j]):
                        self.df_overlap.iloc[i, j] = self.data.iloc[i, j]
                    else:
                        self.df_overlap.iloc[i, j] = np.nan
                else:
                    self.df_overlap.iloc[i, j] = np.nan
        self.eoz_percent = (~self.df_overlap.isna()).sum().sum() / len(self.circle_mat(self.r0 * 5))
        self.df_edge = self.df_overlap.copy()
        edge_list = []
        for i in range(1, self.x_len - 1):
            for j in range(1, self.y_len - 1):
                if not np.isnan(self.df_overlap.iloc[i, j]):
                    if (not np.isnan(self.df_overlap.iloc[i - 1, j])) and (not np.isnan(self.df_overlap.iloc[i, j - 1])) and \
                       (not np.isnan(self.df_overlap.iloc[i + 1, j])) and (not np.isnan(self.df_overlap.iloc[i, j + 1])):
                        self.df_edge.iloc[i, j] = np.nan
                    else:
                        edge_list += [(i, j)]
        angle_list = []
        for i in edge_list:
            x = i[1] - self.y_zero_index
            y = self.x_zero_index - i[0]
            if x == 0:
                theta = 90 if y > 0 else -90
            elif x < 0:
                if y >= 0:
                    theta = np.arctan(y / x) / np.pi * 180 + 180
                else:
                    theta = np.arctan(y / x) / np.pi * 180 - 180
            else:
                theta = np.arctan(y / x) / np.pi * 180
            angle_list += [theta]
        target_list = []
        for i in range(len(angle_list)):
            delta_theta = 0
            target_j = i
            for j in range(len(angle_list)):
                if j != i:
                    angle_y = abs(angle_list[i] - angle_list[j])
                    angle_y  = 360 - angle_y if angle_y > 180 else angle_y
                    if angle_y > delta_theta:
                        delta_theta = angle_y
                        target_j = j
            target_list += [edge_list[target_j]]
        self.edge_para_df['edge_point'] = edge_list
        self.edge_para_df['angle'] = angle_list
        self.edge_para_df['target'] = target_list
    
    def incircle(self):
        edge_list = []
        for i in range(self.x_len):
            for j in range(self.y_len):
                if (i, j) not in self.point_list:
                    self.df_incircle.iloc[i, j] = np.nan
        for point in self.point_list:
            point1, point2, point3, point4 = (point[0] - 1, point[1]), (point[0] + 1, point[1]), (point[0], point[1] - 1), (point[0], point[1] + 1)
            if (point1 in self.point_list) and (point2 in self.point_list) and (point3 in self.point_list) and (point4 in self.point_list):
                pass
                # self.df_incircle.iloc[point[0], point[1]] = np.nan
            else:
                edge_list += [point]
        min_distance_list = []
        for i, j in self.point_list:
            min_distance = 100
            for m, n in edge_list:
                min_distance = min(min_distance, ((i - m) ** 2 + (j - n) ** 2) ** 0.5 * 0.1)
            min_distance_list += [min_distance]
        incircle_r = np.max(min_distance_list)
        index_ = min_distance_list.index(np.max(min_distance_list))
        self.incircle_diatance = (float(self.data.index[self.point_list[index_][0]]) ** 2 + float(self.data.columns[self.point_list[index_][1]]) ** 2) ** 0.5

#         for i in range(self.x_len):
#             for j in range(self.y_len):
#                 if ((self.point_list[index_][0] - i) ** 2 + (self.point_list[index_][1] - j) ** 2) ** 0.5 * 0.1 < incircle_r:
#                     self.df_incircle.iloc[i, j] = 43
        incircle_edge = self.circle_edge(incircle_r * 10)
        for (i, j) in incircle_edge:
            self.df_incircle.iloc[self.point_list[index_][0] + i, self.point_list[index_][1] + j] = np.nan
    
        self.df_incircle.iloc[self.point_list[index_][0] - 1, self.point_list[index_][1] - 1] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0] - 1, self.point_list[index_][1]] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0] - 1, self.point_list[index_][1] + 1] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0], self.point_list[index_][1] - 1] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0], self.point_list[index_][1]] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0], self.point_list[index_][1] + 1] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0] + 1, self.point_list[index_][1] - 1] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0] + 1, self.point_list[index_][1]] = np.nan
        self.df_incircle.iloc[self.point_list[index_][0] + 1, self.point_list[index_][1] + 1] = np.nan
    
    def find_two_point_max(self):
        self.edge_para_df['two_point_mean'] = np.nan
        for i in self.edge_para_df.index:
            self.edge_para_df.loc[i, 'two_point_mean'] = (self.data.iloc[self.edge_para_df.loc[i, 'edge_point'][0], self.edge_para_df.loc[i, 'edge_point'][1]] + self.data.iloc[self.edge_para_df.loc[i, 'target'][0], self.edge_para_df.loc[i, 'target'][1]]) / 2
        
        self.two_point_mean_max = self.edge_para_df['two_point_mean'].max()
        point1 = self.edge_para_df['edge_point'].iloc[self.edge_para_df['two_point_mean'].argmax()]
        point2 = self.edge_para_df['target'].iloc[self.edge_para_df['two_point_mean'].argmax()]
        angle1 = self.edge_para_df[self.edge_para_df['edge_point'] == point1]['angle'].iloc[0]
        angle2 = self.edge_para_df[self.edge_para_df['edge_point'] == point2]['angle'].iloc[0]
        self.two_point_angle = angle1 if (angle1 >= 0 and angle1 < 180) else angle2
        
        pend_index = (self.two_point_angle - 90 - self.edge_para_df['angle']).abs().argmin()
        pend_point1 = self.edge_para_df['edge_point'].iloc[pend_index]
        pend_point2 = self.edge_para_df['target'].iloc[pend_index]
        self.two_point_pend_mean = self.edge_para_df['two_point_mean'].iloc[pend_index]
        if self.two_point_angle - 90 < 0:
            self.two_point_pend_angle = self.two_point_angle + 90
        else:
            self.two_point_pend_angle = self.two_point_angle - 90
        self.two_point_zone_mean = self.zone_cal(point1, point2, True)
        self.two_point_pend_zone_mean = self.zone_cal(pend_point1, pend_point2, True)
    
    def find_zone_max(self):
        self.edge_para_df['zone_mean'] = [self.zone_cal(self.edge_para_df['edge_point'].iloc[i], self.edge_para_df['target'].iloc[i], False) for i in range(len(self.edge_para_df))]

        self.zone_mean_max = self.edge_para_df['zone_mean'].max()
        point1 = self.edge_para_df['edge_point'].iloc[self.edge_para_df['zone_mean'].argmax()]
        point2 = self.edge_para_df['target'].iloc[self.edge_para_df['zone_mean'].argmax()]
        angle1 = self.edge_para_df[self.edge_para_df['edge_point'] == point1]['angle'].iloc[0]
        angle2 = self.edge_para_df[self.edge_para_df['edge_point'] == point2]['angle'].iloc[0]
        self.zone_angle = angle1 if (angle1 >= 0 and angle1 < 180) else angle2
        
        pend_index = (self.zone_angle - 90 - self.edge_para_df['angle']).abs().argmin()
        pend_point1 = self.edge_para_df['edge_point'].iloc[pend_index]
        pend_point2 = self.edge_para_df['target'].iloc[pend_index]
        self.zone_pend_mean = self.edge_para_df['zone_mean'].iloc[pend_index]
        if self.zone_angle - 90 < 0:
            self.zone_pend_angle = self.zone_angle + 90
        else:
            self.zone_pend_angle = self.zone_angle - 90
    
    def find_ring_max(self):
        for i in range(self.x_len):
            for j in range(self.y_len):
                dis_zero = ((i - self.x_zero_index) ** 2 + (j - self.y_zero_index) ** 2) ** 0.5 * 0.1
                if dis_zero < self.r0 / 2:
                    self.ring_overlap.iloc[i, j] = self.data.iloc[i, j]
                else:
                    self.ring_overlap.iloc[i, j] = np.nan
        self.ring_edge = self.ring_overlap.copy()
        edge_list = []
        for i in range(1, self.x_len - 1):
            for j in range(1, self.y_len - 1):
                if not np.isnan(self.ring_overlap.iloc[i, j]):
                    if (not np.isnan(self.ring_overlap.iloc[i - 1, j])) and (not np.isnan(self.ring_overlap.iloc[i, j - 1])) and \
                       (not np.isnan(self.ring_overlap.iloc[i + 1, j])) and (not np.isnan(self.ring_overlap.iloc[i, j + 1])):
                        self.ring_edge.iloc[i, j] = np.nan
                    else:
                        edge_list += [(i, j)]
        angle_list = []
        for i in edge_list:
            x = i[1] - self.y_zero_index
            y = self.x_zero_index - i[0]
            if x == 0:
                theta = 90 if y > 0 else -90
            elif x < 0:
                if y >= 0:
                    theta = np.arctan(y / x) / np.pi * 180 + 180
                else:
                    theta = np.arctan(y / x) / np.pi * 180 - 180
            else:
                theta = np.arctan(y / x) / np.pi * 180
            angle_list += [theta]
        target_list = []
        for i in range(len(angle_list)):
            delta_theta = 0
            target_j = i
            for j in range(len(angle_list)):
                if j != i:
                    angle_y = abs(angle_list[i] - angle_list[j])
                    angle_y  = 360 - angle_y if angle_y > 180 else angle_y
                    if angle_y > delta_theta:
                        delta_theta = angle_y
                        target_j = j
            target_list += [edge_list[target_j]]
        self.ring_para_df['edge_point'] = edge_list
        self.ring_para_df['angle'] = angle_list
        self.ring_para_df['target'] = target_list
        
        self.ring_para_df['ring_mean'] = np.nan
        for i in self.ring_para_df.index:
            self.ring_para_df.loc[i, 'two_point_mean'] = (self.data.iloc[self.ring_para_df.loc[i, 'edge_point'][0], self.ring_para_df.loc[i, 'edge_point'][1]] + self.data.iloc[self.ring_para_df.loc[i, 'target'][0], self.ring_para_df.loc[i, 'target'][1]]) / 2
        
        self.ring_mean_max = self.ring_para_df['two_point_mean'].max()
        point1 = self.ring_para_df['edge_point'].iloc[self.ring_para_df['two_point_mean'].argmax()]
        point2 = self.ring_para_df['target'].iloc[self.ring_para_df['two_point_mean'].argmax()]
        angle1 = self.ring_para_df[self.ring_para_df['edge_point'] == point1]['angle'].iloc[0]
        angle2 = self.ring_para_df[self.ring_para_df['edge_point'] == point2]['angle'].iloc[0]
        self.ring_angle = angle1 if (angle1 >= 0 and angle1 < 180) else angle2
        
        pend_index = (self.ring_angle - 90 - self.ring_para_df['angle']).abs().argmin()
        pend_point1 = self.ring_para_df['edge_point'].iloc[pend_index]
        pend_point2 = self.ring_para_df['target'].iloc[pend_index]
        self.ring_pend_mean = self.ring_para_df['two_point_mean'].iloc[pend_index]
        if self.ring_angle - 90 < 0:
            self.ring_pend_angle = self.ring_angle + 90
        else:
            self.ring_pend_angle = self.ring_angle - 90
    
    def plot(self):
        fig, axs = plt.subplots(3, 2, figsize=(10, 12))
        sns.heatmap(self.data, ax=axs[0, 0])
        sns.heatmap(self.smooth_data_with_min_for_plot, ax=axs[0, 1])
        sns.heatmap(self.df_incircle, ax=axs[1, 0])
        sns.heatmap(self.two_point_zone_for_plot, ax=axs[1, 1])
        sns.heatmap(self.ring_overlap, ax=axs[2, 0])
        plt.show()
    
    @staticmethod
    def circle_mat(r):
        circle_point_list = []
        for i in range(-math.ceil(r), math.ceil(r) + 1):
            for j in range(-math.ceil(r), math.ceil(r) + 1):
                if i ** 2 + j ** 2 <= r ** 2:
                    circle_point_list += [(i, j)]
        return circle_point_list
    
    @staticmethod
    def circle_edge(r):
        circle_edge_list = []
        for i in range(-math.ceil(r), math.ceil(r) + 1):
            for j in range(-math.ceil(r), math.ceil(r) + 1):
                if i ** 2 + j ** 2 <= r ** 2:
                    if (i - 1) ** 2 + j ** 2 > r ** 2 or (i + 1) ** 2 + j ** 2 > r ** 2 or \
                        i ** 2 + (j - 1) ** 2 > r ** 2 or i ** 2 + (j + 1) ** 2 > r ** 2:
                        circle_edge_list += [(i, j)]
        return circle_edge_list
    
    def zone_cal(self, point1_, point2_, plot=False):
        zone_sum = 0
        zone_n = 0
        count = 0
        k = (point1_[0] - point2_[0]) / (point1_[1] - point2_[1]) if point1_[1] - point2_[1] != 0 else np.inf        
        if abs(k) <= 1:
            for i in range(self.y_len):
                j = round(k * (i - self.y_zero_index) + self.x_zero_index)
                if j <= max(point1_[0], point2_[0]) and j >= min(point1_[0], point2_[0]):
                    if i <= max(point1_[1], point2_[1]) and i >= min(point1_[1], point2_[1]):
                        if plot:
#                             if count % 3 != 0:
                            self.two_point_zone_for_plot.iloc[j, i] = np.nan
                            count += 1
                        zone_sum += self.data.iloc[j, i]
                        zone_n += 1
        if abs(k) > 1:
            for i in range(self.x_len):
                j = round(1 / k * (i - self.x_zero_index) + self.y_zero_index)
                if j <= max(point1_[1], point2_[1]) and j >= min(point1_[1], point2_[1]):
                    if i <= max(point1_[0], point2_[0]) and i >= min(point1_[0], point2_[0]):
                        if plot:
#                             if count % 3 != 0:
                            self.two_point_zone_for_plot.iloc[i, j] = np.nan
                            count += 1
                        zone_sum += self.data.iloc[i, j]
                        zone_n += 1
        return zone_sum / zone_n

a = Patient('data/', 'Li_Minfeng_OD_27032023_094446_CUR.CSV')

ui.page_opts(title="EOZ-Merging-Method", fillable=True)

colors_list = ['#A2FAFF','#02EFFF','#00C8FE','#008CFF','#0000FD','#0001B3','#003198','#0001B4','#003294','#00627A',
               '#055F57','#006F00','#009A00','#00AB00','#46ED00','#BBFF00','#FFFE00','#FFC404','#F89900','#FB6302',
               '#FE0000','#CA0000','#940039','#A30099','#EE00DA','#FF44FF','#FFACFF','#C8C8C8','#979797','#646464','#0C0C0C']
n_bins = 1000
cmap = colors.LinearSegmentedColormap.from_list('custom_cmap', colors_list, N=n_bins)

# Add main content
ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "ellipsis": fa.icon_svg("ellipsis"),
}

with ui.layout_columns(col_widths=[3, 3, 3, 3], fill=False):
    # with ui.value_box(showcase=ICONS["user"]):
    #     "Total tippers"
    #     @render.express
    #     def total_tippers():
    #         2333
            
    with ui.value_box(fill=False):
        "angle1"
        @render.express
        def total_tippers():
            a.two_point_angle
            
    with ui.value_box(fill=False):
        "k1"
        @render.express
        def total_tippers():
            a.two_point_mean_max
            
    with ui.value_box(fill=False):
        "angle2"
        @render.express
        def total_tippers():
            a.two_point_pend_angle
            
    with ui.value_box(fill=False):
        "k2"
        @render.express
        def total_tippers():
            a.two_point_pend_mean

with ui.layout_columns(col_widths=[6], fill=False):

    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Total bill vs tip"

        @render_plotly
        def scatterplot():
            color = input.scatter_color()

            z = [[1, 2, 3, ], [4, 5, 6]]
            fig = px.imshow(z)#a.data.fillna(0).iloc[10: -9, 8: -10].values.tolist())#, color_continuous_scale="Viridis")
            return fig
            
            # fig, ax = plt.subplots(figsize=(6, 4))
            # plt.imshow(a.data.iloc[10: -9, 8: -10], cmap=cmap, interpolation='nearest', vmin=32, vmax=47,)
            # plt.xticks(np.arange(0,121,20), np.arange(-6, 7, 2))
            # plt.yticks(np.arange(0,121,20), np.arange(-6, 7, 2))
            # plt.grid(True, color='grey', linestyle='--', alpha=0.5)
            # plt.colorbar()

            # fig_plotly = tls.mpl_to_plotly(fig)
            # return fig_plotly
            
            # return px.scatter(
            #     tips_data(),
            #     x="total_bill",
            #     y="tip",
            #     color=None if color == "none" else color,
            #     trendline="lowess",
            # )
