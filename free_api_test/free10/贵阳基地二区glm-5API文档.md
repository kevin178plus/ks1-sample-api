glm-5 API文档
更新时间： 2026-02-12 21:38:40
glm-5
glm-5专注于复杂系统工程和长周期智能体任务。与上一代模型 glm-4.7相比，glm-5 的参数量从 355B（激活参数 32B）扩展至 744B（激活参数 40B）。此外，glm-5 还集成了 DeepSeek 稀疏注意力（DSA）机制，在保持长上下文能力的同时大幅降低了部署成本。
接口描述
通过调用本接口，来实现对glm-5的对话请求



域名列表
调用不同云区域的模型，请使用不同的域名

支持的云区域	域名
贵阳基地二区	 https://aigw-gzgy2.cucloud.cn:8443
鉴权说明
服务使用api key进行鉴权。

api key获取方式：控制台创建服务，然后创建api key，创建时关联api key与服务。

请求结构
curl -X POST https://[域名地址]/v1/chat/completions -H "Authorization: [使用的apikey]" -H "Content-Type: application/json" -d '{
  "model": "glm-5",
  "messages": [
    {"role": "user", "content": "国产GPU和英伟达的区别?"}
  ],
  "stream": true
}'

请求头域
除公共头域外，增加了apikey头域。

请求参数
Body参数

名称	类型	是否必填	描述
model	string	是	使用的模型名称
messages	List(message)	是	消息列表，其中每条消息必须包含 role和 content。
temperature	float	否	控制生成的文本的创造性。较高的值（如 0.8）将使输出更随机，而较低的值（如 0.2）则更加集中和确定。
top_p	float	否	一种替代 temperature 的采样方法。top_p 会根据累积概率选择 token，1 表示考虑所有 token。
n	int	否	生成的回复数量
stream	bool	否	是否开启流式响应。若为 true，响应会逐步返回部分内容。
stop	List(string)	否	停止生成的字符串，支持字符串数组（如 ["\n"]）。
max_tokens	int	否	单次请求生成的最大 token 数。
presence_penalty	int	否	是否鼓励生成新主题。值为 -2.0 至 2.0 之间，正值增加生成新话题的可能性。
frequency_penalty	int	否	控制生成重复 token 的可能性。值为 -2.0 至 2.0 之间，正值减少重复。
logit_bias	int	否	用于调整特定 token 出现的概率。接受一个 map，key 是 token 的 ID，值是从 -100 到 100 的数值。
user	string	否	用户 ID，用于标识请求来源的用户。
message说明

名称	类型	是否必填	描述
role	string	是	角色，包括以下： system：用于设定助手的行为，如“你是一个帮助用户解决问题的助手”。 user：表示用户输入 assistant：表示助手回复
content	string	是	对话内容
响应参数
名称	类型	描述
id	string	每次生成的回复的唯一标识符。
object	string	响应对象类型，如 "chat.completion"。
created	int	响应的生成时间戳。
model	string	使用的模型名称。
choices	List(CompletionsChoice)	返回的生成文本选项列表。
usage	CompletionsUsage	token 使用情况。
CompletionsChoice说明
名称	类型	描述
finish_reason	string	生成结束的原因，如 stop（正常结束）、length（达到最大 token 长度）。
index	int	响应对象类型，如 "chat.completion"。
message	CompletionsAssistantMessage	包含生成的消息。
CompletionsAssistantMessage说明

名称	类型	描述
content	string	返回的对话内容
role	string	对话助手的角色
CompletionsUsage说明
名称	类型	描述
completion_tokens	string	生成对话的 token 数量
prompt_tokens	string	问题的token 数量
total_tokens	string	总 token 数量
其中流式模式的相应参数与非流式模式的响应参数有所不同

流式模式：响应为多个字段，每个字段的相应参数为data:{响应参数}。

非流式模式：响应为以为字段的完整json包

请求示例（流式）
curl -X POST https://aigw-sh22.cucloud.cn/v1/chat/completions -H "Authorization: REVOKED_KEY" -H "Content-Type: application/json" -d '{
  "model": "glm-5",
  "messages": [
    {"role": "user", "content": "国产GPU和英伟达的区别?"}
  ],
  "stream": true, "max_tokens": 20
}'
响应示例（流式）
data: {"choices":[{"delta":{"content":"","role":"assistant"},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: {"choices":[{"delta":{},"finish_reason":"length","index":0}],"created":1770895927,"id":"chatcmpl-ab30b6ae1214ea26","model":"glm-5","object":"chat.completion.chunk"}

data: [DONE]                                                                                                                                                                                                                      


非流式请求示例
curl -X POST https://aigw-sh22.cucloud.cn/v1/chat/completions -H "Authorization: REVOKED_KEY" -H "Content-Type: application/json" -d '{
  "model": "glm-5",
  "messages": [
    {"role": "user", "content": "国产GPU和英伟达的区别?"}
  ],
  "stream": false, "max_tokens": 20
}'
响应示例
{"choices":[{"finish_reason":"length","index":0,"message":{"content":null,"role":"assistant","tool_calls":[]}}],"created":1770895980,"id":"chatcmpl-955cda9535ab59c2","model":"glm-5","object":"chat.completion","usage":{"completion_tokens":20,"prompt_tokens":13,"prompt_tokens_details":null,"total_tokens":33}} 
