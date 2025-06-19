
import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_deepseek import ChatDeepSeek
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
import http.client
import json


# Load environment variables
load_dotenv()

class MyCustomHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"\n🤖 AI正在思考...", end="", flush=True)
        
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(token, end="", flush=True)  # 直接打印token，不添加额外信息
        
    def on_llm_end(self, response, **kwargs):
        print(f"\n\n✅ 回答完成！")
        
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown")
        print(f"\n🔧 正在使用工具: {tool_name}")
        
    def on_tool_end(self, output, **kwargs):
        print(f"✅ 工具执行完成")


llm = ChatDeepSeek(
    temperature=0, # temperature=0 表示输出更加确定性，不会随机性太强
    model="deepseek-chat", # 指定使用的模型名称
    api_key=os.getenv("DEEPSEEK_API_KEY"),# 从环境变量中获取 API 密钥
    #  streaming=True,callbacks=[MyCustomHandler()]
 )

search_tool = TavilySearchResults(max_results=3)

@tool
def play_pic(tvCode: str, url: str):
    """
        播放图片
            参数:
                tvCode: 电视投屏码
                url: 图片链接
            返回:
                推送结果
    """

    data = lebo_push(tvCode, url,"image")
    data = json.loads(data.decode("utf-8"))
    if data.get("code") == 0:
        return "播放成功"
    else:
        return "播放失败"

@tool
def play_video(tvCode: str, url: str):
    """
        播放视频
            参数:
                tvCode: 电视投屏码
                url: 视频链接
            返回:
                推送结果
    """

    data = lebo_push(tvCode, url,"video")
    data = json.loads(data.decode("utf-8"))
    if data.get("code") == 0:
        return "播放成功"
    else:
        return "播放失败"



def lebo_push(tvCode: str, url: str,mediaType: str):
    conn = http.client.HTTPSConnection("saas.hpplay.cn")
    payload = json.dumps({
    "playId": "1",
    "action": "set-playlist",
    "expired": 10000,
    "playlist": [
        {
            "name": "",
            "mediaType": mediaType,
            "urls": [
                {
                "id": "1",
                "resolution": "HD",
                "url": url,
                "height": 0,
                "width": 0
                }
            ]
        }
    ]
    })

    headers = {
        'Authorization': 'Bearer '+"xxx",
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/lebo-open/v2/push?appId=23340&sessionId=12321sdasda1232131231&uid=90001799436462&tvCode="+tvCode, payload, headers)
    res = conn.getresponse()
    data = res.read()
    return data


tools = [search_tool, play_pic, play_video]

llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages([
	("system","你是一个高效的助手。请使用可用的工具来回答用户的问题。",),
	MessagesPlaceholder(variable_name="chat_history"),
	("human", "{input}"),
	MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),])

# 创建记忆组件
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)


agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools,memory=memory)

if __name__ == "__main__":

    questions = [
        "我的电视投屏码是68297929",
        "播放图片 图片链接是http://gips3.baidu.com/it/u=3886271102,3123389489&fm=3028&app=3028&f=JPEG&fmt=auto?w=1280&h=960",
        "播放视频 视频链接是 https://business-video.oss-cn-shenzhen.aliyuncs.com/px/喜羊羊与灰太狼之发明大作战/喜羊羊与灰太狼之发明大作战01寻找妙多多-上.mp4",
        "我的投屏码是多少？"
    ]
    for question in questions: 
        print(f"\nQuestion: {question}")
        response = agent_executor.invoke({"input": question})
        print(f"Answer: {response['output']}")
