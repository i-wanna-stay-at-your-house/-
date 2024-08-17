import openai
import click
import json
import os
import yaml
import pandas as pd

# 엑셀 파일 경로
file_path = r'C:\Users\user\Desktop\경희대\학부연구생\주담대dataset.xlsx'

# 특정 시트(input_sample)만
# CSV 파일 읽기
# df.to_csv('output.csv', index=False, encoding='utf-8-sig')
# d = pd.read_csv('output.csv', encoding='utf-8-sig')

#인코딩이 잘 안 돼서 한글이 깨지긴 하는데,,, python은 인덱싱도 잘하고 잘 읽고 있는 것 같으니 그냥 진행


# 환경 변수에서 API 키를 가져옵니다.
api_key = os.getenv('OPENAI_API_KEY')  
openai.api_key = api_key

client = openai
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")


def extract_keywords(content):
    # GPT-4o-mini 모델을 사용해 키워드 추출
    prompt = (
        f"다음 텍스트에서 주제에 맞는 가장 중요한 단어들을 개수에 상관없이 추출해줘:\n\n"
        f"\"{content}\"\n\n"
        "추출한 단어들은 쉼표로 구분해줘."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )
    
    #choices[0]은 실질적 대답의 내용
    keywords = completion.choices[0].message.content
    return keywords.split(",")

    

def augment_article(title, content, keywords):
    prompt = (
        f"기사 제목: {title}\n"
        f"기사 본문: {content}\n"
        f"특성: {keywords}\n\n"
        "위 내용을 바탕으로 1000자 정도의 기사를 작성하시오. "
        "실존하는 내용으로만 작성하고, 통계 자료를 사용한다면 출처 자료 링크를 꼭 남겨주세요."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content.strip()



def classify_article(title, augment_content):
    """
    Classifies the article into predefined categories based on the title and content.
    """

    # 프롬프트 구성
    p1 = f"{title}\n\n{augment_content}" 
    
    p2 = f"위 기사는 다음 카테고리 중 어디에 해당되는가?:\n" \
         "금리상승\n금리하락\n금리유지\n대출실시/재개\n대출제한/중단\n대출금액증가\n대출금액감소\n" \
         "주택가격상승\n주택가격하락\n연체율 상승\n연체율 하락\n주택거래증가\n주택거래감소\n" \
         "경기침체\n경제활성화\n대출조건강화\n대출조건완화\n대출상환가속\n금리비교서비스\n정책\n기타\n\n" 
    
    p3 = f"""결과를 다음과 같은 형식으로 제시하라. "value1"에 예측 가능한 값을 배치하고 가장 확실한 2개의 값만을 제시하라. 선정 이유는 "value2"에 제시하라.\n{{"category1":"value1", "reason1":"value2","category2":"value2"}}"""
    
    prompt = p1 + p2 + p3
         
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 경제 상식에 해박한 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # 응답에서 결과 추출
    result_text = completion.choices[0].message.content.strip()

    try:
        # JSON 형식으로 파싱
        result_json = json.loads(result_text)
        print(json.dumps(result_json, indent=4, ensure_ascii=False))
    except json.JSONDecodeError:
        print("Error: The model's response could not be parsed as JSON.")
        print(result_text)

#cli 입력 부분
@click.command()
@click.option('--file_path', prompt='Excel file path', help='The path to the Excel file.')
@click.option('--sheet_name', prompt='Sheet name', help='The name of the sheet to access.')

def main(file_path, sheet_name):
    
    try:
        # Excel 파일에서 특정 시트 읽기
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # 데이터 출력 (예: 첫 5개 행)
        print(df.head())
    except Exception as e:
        print(f"An error occurred: {e}")
    
    for num in range(len(df["UUID"])):
        keywords = extract_keywords(df["Content"][num])
        print("Extracted Keywords:", keywords)

        augmented_article = augment_article(df["Title"][num], df["Content"][num], keywords)
        print("Augmented Article:\n", augmented_article)

        classify_article(df["Title"][num], augmented_article)

if __name__ == '__main__':
    main()