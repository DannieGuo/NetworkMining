import csv
import jieba.posseg
import json
import networkx as nx

# 数据预处理: 分词, 提取, 统计
def Preprocess_Extract(origin_file_name, relation_file_name):
    print("first preprocess ...")

    co_occur = {} #共同出现次数
    word_type = ['nr', 'nrfg', 'nrt'] #人名
    # word_type = ['nr', 'nrfg', 'nrt', 'nt', 'nz'] #人名、地名、机构
    text_type = ['title', 'text'] #只需要标题和正文

    with open(origin_file_name, encoding = "utf-8") as f:
        reader = csv.reader(f, delimiter = '\t') #每一行为一条新闻，其中各个字段用\t 隔开

        for i, row in enumerate(reader): #i是下标，第几条新闻 row就是该条新闻内容
            if i == 0:
                text_type = [row.index(attri) for attri in text_type]
                continue

            # 提取标题和正文中的实体
            news_entity = set()
            for attri in text_type: 
                cut_result = jieba.posseg.cut(row[attri])
                for word, flag in cut_result:
                    if flag in word_type:
                        news_entity.add(word)

            # 统计该新闻中的联系
            for entity in news_entity:
                for other in news_entity:
                    try:
                        co_occur[entity][other] += 1
                    except:
                        try:
                            co_occur[entity][other] = 1
                        except:
                            co_occur[entity] = {}
                            co_occur[entity][other] = 1

    # 保存数据
    json_str = json.dumps(co_occur, ensure_ascii = False, indent = 2)
    with open(relation_file_name, 'w') as json_file:
        json_file.write(json_str)   

    print("first preprocess finished.")


# 读取存在json文件里的关系并转换为dict
def Read_Json(relation_file_name):
    print("read json begin")
    with open(relation_file_name, 'r', encoding = "utf-8") as f:
        relation = json.load(f)
    print("read done")
    return relation

# 建立社交网络图
def Preprocess_Create_Graph(relation):
    print("create graph")
    G = nx.Graph()
    for entity in relation.keys():
        for other in relation[entity]:
            if entity == other:
                continue
            G.add_edge(entity, other, weight = relation[entity][other])
    print("create graph finished.")
    return G


# 热门人物和机构
def Hot_Entity(relation):
    print('top 20 hot entity')
    entitys = []
    for entity in relation.keys():
        entitys.append([entity, relation[entity][entity]])
    entitys = sorted(entitys, key = lambda item: item[1], reverse = True)
    print(entitys[:20])  


# 输出和 A 关系最强的前 10 个人
def Closest_Neighbour(relation):
    while(True):
        Node = input('输入结点名称（输入quit退出）: ')
        if Node == 'quit':
            break
        if Node in relation == False:
            print("该结点不存在:", Node)
            continue
        
        # 检索邻居并排序
        tmp = relation[Node] #是个字典, 第一个是字符, 第二个是共同出现次数
        # 用共同出现次数作为key来排序, 降序排序
        tmp = sorted(tmp.items(), key = lambda item: item[1], reverse = True)
        # 输出关系最强的10个邻居
        print("top closest 10 neighbor of ", Node)
        cnt = 0
        for elem in tmp:
            if elem[0] == Node: #自身
                continue
            print(elem)
            cnt += 1
            if cnt == 10:
                break


# 统计:图的结点个数, 边数, 连通分量的个数, 最大连通分量的大小
def Graph_Detail(G):
    print("graph details:")
    print('结点数：', len(G.nodes))
    print('边数：', len(G.edges))
    cc = list(nx.connected_components(G)) #无向图的连通分量
    print('连通分量个数：', len(cc)) 
    print('极大连通分支：', len(max(cc, key = lambda elem : len(elem))))


# 影响力计算
def Node_PageRank(G):
    print("top 20 influential people : ")
    page_rank = nx.pagerank(G, alpha = 0.85) #所有结点的pagerank
    page_rank = sorted(page_rank.items(), key = lambda item:item[1], reverse = True) #排序
    print(page_rank[:20])  

# 计算路径权重和
def Get_Path_Weight(G, path):
    sum = 0
    for i in range(len(path) - 1):
        sum = sum + G[path[i]][path[i + 1]]['weight']
    return sum

#小世界理论验证: AB间的前10条最优路径
def Mini_World(G):
    Node1 = ''
    Node2 = ''
    while(True):
        Node1 = input('输入结点1名称（输入quit退出）: ')
        if Node1 == 'quit':
            break
        if G.has_node(Node1) == False:
            print("该结点不存在: ", Node1)
            continue

        Node2 = input('输入结点2名称（输入quit退出）: ')
        if Node2 == 'quit':
            break
        if G.has_node(Node2) == False:
            print("该结点不存在: ", Node2)
            continue

        #求出AB的所有路径
        all_paths = nx.all_shortest_paths(G, source = Node1, target = Node2)
        all_paths = list(all_paths)

        sorted(all_paths, key = lambda item: (len(item), -Get_Path_Weight(G, item)), reverse = False)
        print("top 10 shorest path between ", Node1, " and ", Node2)
        print(all_paths[:10])

#小世界理论验证: 任意两个人之间的平均路径长度
def Avg_Path_Len(G):
    print("average path length: ")
    sum = 0
    # 对每一个连通分量计算平均路径长度
    for c in sorted(nx.connected_components(G), key = len, reverse = False):
        nodes_num = len(c)
        subG = G.subgraph(c)
        sub_avg = nx.average_shortest_path_length(subG)
        sum = sum + sub_avg * nodes_num
    # 全图平均路径长度
    print(sum / nx.number_of_nodes(G))

# 中心性计算
def Node_Centrality(G):
    print("top 10 betweenness centrality people")
    betweenness = nx.betweenness_centrality(G)
    betweenness = sorted(betweenness.items(), key = lambda item:item[1], reverse = True)
    print(betweenness[:10])

# 聚集系数计算
def Node_Cluster(G):
    print("top 10 clustering people")
    clustering_factor = nx.clustering(G)
    clustering_factor = sorted(clustering_factor.items(), key = lambda item:item[1], reverse = True)
    print(clustering_factor[:10])


# 一、数据预处理
relation_file_name = r"C:\Users\74285\Desktop\网群大作业\gov_news\relation_people.json"
# origin_file_name = r"C:\Users\74285\Desktop\网群大作业\gov_news\gov_news.txt"
# Preprocess_Extract(origin_file_name, relation_file_name)

# 生成图数据
relation = Read_Json(relation_file_name)
G = Preprocess_Create_Graph(relation)

# 热门人物
Hot_Entity(relation)


# 二、图的验证、图的统计、影响力计算
# 图的验证：关系最近的10个人
Closest_Neighbour(relation)

# 图的统计：图的结点个数，边数，连通分量的个数，最大连通分量的大小
Graph_Detail(G)

# 影响力计算(PageRank)：影响力最大的前20个人
Node_PageRank(G)

# 三、自选分析：小世界理论验证、中心性计算、聚集系数计算
# 小世界理论验证
Avg_Path_Len(G)
Mini_World(G)

# 中心性计算: 中介中心性最大的10个人
Node_Centrality(G)

# 聚集系数计算：聚集系数最大的10个人
Node_Cluster(G)