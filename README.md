ytb2xhs

一个将 YouTube 视频内容 转换成 小红书风格笔记文案 的小工具。

使用方法
1. 克隆代码
git clone https://github.com/cacasasasa/ytb2xhs.git
cd ytb2xhs

2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt

3. 配置 API Key

在项目根目录下新建一个 .env 文件，写入：

OPENAI_API_KEY=sk-xxxx

4. 运行
python main.py


然后输入 YouTube 视频链接，程序会自动生成对应的小红书文案。

示例

输入：

https://www.youtube.com/watch?v=q6kJ71tEYqM


输出：

### 机器学习 vs 深度学习，谁更胜一筹？🍕🤖
想知道机器学习和深度学习之间的区别吗？今天就用比萨饼来解密！
...
