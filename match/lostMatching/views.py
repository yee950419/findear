from django.shortcuts import render
from django.http import JsonResponse
import json
import pandas as pd
# from numpyencoder import NumpyEncoder
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import re
from . import matching

# Create your views here.

def lost_matching(request):
    if request.method == 'POST':
        # try:
        #     body = json.loads(request.body)
        # except JSONDecodeErorr:
        #     return JsonResponse({'error':'invalid json'}, status=400)
        body = json.loads(request.body)
        data = process_lost_item_data(body)
    return JsonResponse({ 'message':'success', 'result':data }, status = 200)

def process_lost_item_data(found_item_info):
    # 받은 데이터를 이용하여 DataFrame 생성
    df = pd.DataFrame([found_item_info])

    # 데이터 처리 수행
    processed_data = analyze_lost_data(df)

    return processed_data

def analyze_lost_data(data):
    # 데이터 분석 수행
    return data

def findear_matching(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error':'invalid json'}, status=400)
        result = process_findear_item_data(body)
        result = [{"lostBoardId" : body["lostBoard"]["lostBoardId"]}] + result
    else:  # post 요청이 아닐 경우
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
   
    return JsonResponse({ 'message':'success', 'result':result }, status = 200)

def process_findear_item_data(items_info):
    # 코드 실행 시작 시간 측정
    start_time = time.time()
    
    lostBoard = items_info["lostBoard"]
    acquiredBoardList = items_info["acquiredBoardList"]
    
    # # 받은 데이터를 이용하여 DataFrame 생성
    # df = pd.DataFrame(items_info["acquiredBoardList"])
    
    # 데이터 처리 수행
    processed_data = matching.findear_matching(lostBoard, acquiredBoardList)
    # processed_data = analyze_findear_data(df)
    
    # 코드 실행 종료 시간 측정
    end_time = time.time()

    # 시작 시간과 종료 시간의 차이를 계산하여 실행 시간 출력
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time} 초")
    
    return processed_data

# 삭제 예정
def analyze_findear_data(data):
    # 데이터 분석 수행
    data_list = [
		{
			"lostBoardId" : 1,
			"acquiredBoardId" : 1,
			"simulerityRate" : 0.9
		},
		{
			"lostBoardId" : 1,
			"acquiredBoardId" : 2,
			"simulerityRate" : 0.8
		},
		{
			"lostBoardId" : 1,
			"acquiredBoardId" : 5,
			"simulerityRate" : 0.9
		}
	]
    return data_list

# 게시글 이미지 정보 추출
def image_process(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:  # body 데이터가 json이 아닐 경우
            return JsonResponse({'error':'invalid json'}, status=400)
        if body.get("productName") and body.get("imgUrls"):  
            product_name = body["productName"]
            image_url = body["imgUrls"][0]
            result = process_execute(product_name, image_url)
        else:  # 적절한 body 데이터가 아닐 경우
            return JsonResponse({'error': 'Incorrect request body'}, status=400)
    else:  # post 요청이 아닐 경우
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
            
    return JsonResponse({ 'message':'success', 'result':result }, status = 200)
    

def process_execute(product_name, image_url):
    # 코드 실행 시작 시간 측정
    start_time = time.time()

    load_dotenv()

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    
    question_text = f"""
    분실물에 대한 여러 정보를 제공하려고 해.
    물품명은 '{product_name}'야.
    사진 속 가장 중심이 되는 물체를 물품명을 포함해 분석하여 다음의 형식에 맞춰 제공해줘.

    - 물체의 카테고리(카드, 지갑, 현금, 의류, 전자기기, 가방, 휴대폰, 증명서, 쇼핑백, 귀금속, 유가증권, 자동차, 서류, 도서용품, 스포츠용품, 컴퓨터, 산업용품, 악기, 기타 중 하나)
    - 물체의 색상 1가지(화이트, 블랙, 레드, 오렌지, 옐로우, 그린, 블루, 브라운, 퍼플, 핑크, 그레이, 기타 중 하나)
    - 물체 외형 특징에 대한 추가 키워드 5개
    {{
        "category" : "카테고리명",
        "color" : "색상명"
        "description" : ["키워드1", "키워드2", ... ]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON. Give only JSON"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "low"
                        }
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # gpt 답변 중 내용만 추출
    gpt_content = response.choices[0].message.content
    # usage_token = response['usage']['total_tokens']
    print("내용 : ", gpt_content)

    # 내용 중 중괄호 사이의 문자열 추출
    match = re.search(r'{(.+)}', gpt_content, re.DOTALL)
    result_data = json.loads(match.group(0))
    print(result_data)

    # 코드 실행 종료 시간 측정
    end_time = time.time()

    # 시작 시간과 종료 시간의 차이를 계산하여 실행 시간 출력
    execution_time = end_time - start_time
    print(f"실행 시간: {execution_time} 초")
    return result_data