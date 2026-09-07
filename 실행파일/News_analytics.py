# -*- coding: utf-8 -*-
"""
News_analytics.py
====================================================================
네이버 뉴스(언론사별) 자동 수집 → 명사 빈도 분석 → 시각화(PNG) → 인사이트 CSV 저장

[처리 개요]
    1) PRESS_LIST 에 정의된 언론사 × CATEGORIES 에 정의된 카테고리(정치/경제/사회/
       생활문화/세계/IT과학 + 주요뉴스/이슈) 조합마다 네이버 뉴스(언론사 홈) 페이지에서
       당일 기사 제목과 링크를 수집한다.
    2) 기본적으로 각 기사 상세 페이지(`#dic_area`)에서 본문까지 가져와 제목과 함께
       분석 대상 텍스트로 사용한다 (fetch_article_text, 아래 4번 항목 참고).
    3) kiwipiepy 로 형태소 분석하여 명사(일반/고유명사)만 추출하고, STOPWORDS(보도체
       상투어·시간 표현·범용 추상명사 등)를 제거한 뒤 상위 100개 빈도를 집계한다.
       이 전처리(불용어 제거)는 막대그래프·워드클라우드 양쪽에 동일하게 반영된다 —
       두 시각화가 공통으로 extract_noun_counter()의 결과(counter)를 그대로 사용하기
       때문이다.
    4) 신문사 x 카테고리 조합마다 그래프 4종(PNG, 모두 제목 포함)과 CSV 2종을 저장한다.
         (1) 빈도수 워드클라우드   (2) 빈도수 바차트 TOP 20
         (3) 감성분석 워드클라우드 (4) 감성분석 바차트 (긍정 Top10 + 부정 Top10 = 20개)
         (5) 키워드빈도 CSV        (6) 감성분석기초자료 CSV
       감성 분석은 3)에서 만든 명사 Counter(불용어 제거 완료)를 그대로 재사용하며,
       POSITIVE_WORDS / NEGATIVE_WORDS 사전에 걸린 단어만 대상으로 한다.
       색상 규칙: 긍정 = 진한 남청색 -> 옅은 청색, 부정 = 진한 빨강 -> 옅은 빨강
       (두 경우 모두 빈도 1위가 가장 진한 색).
       제목 형식: [날짜 - (신문사/종합) - 카테고리 - 분석 유형]
    4-1) 하루치 전 신문사 x 전 카테고리 결과를 합산해 날짜 폴더 바로 아래
       (News/{YYYY}/{MM}/{DD}/)에 일 단위 산출물을 저장한다 (build_daily_summary).
         - 그래프 4종 + CSV 2종 (개별과 동일 규격)
         - 일간종합_인사이트_{YYYYMMDD}.txt : 개요/핵심키워드/감성/신문사별/
           카테고리별/공통 의제/단독 키워드까지 풀어쓴 상세 리포트
         - 일간종합_인사이트_{YYYYMMDD}.csv : 종합·신문사별·카테고리별·조합별
           지표를 한 행씩 담은 집계용 표(감성지수 포함)
    5) 규칙 기반 인사이트 문장을 생성하여 CSV로 저장한다.
       (txt가 아닌 CSV로 저장하는 이유: 엑셀/BI 도구에서 바로 열람·집계하기 위함)
    6) 저장 경로: News/{YYYY}/{MM}/{DD}/{언론사}/{카테고리}/
       예) News/2026/08/31/조선일보/경제/
    7) 여러 날짜의 insight_master.csv를 이어붙이면 시계열 키워드 트렌드 분석,
       언론사 간 이슈 비교로 바로 확장할 수 있다 (README.md 8번 항목의 pandas 예시 참고).

[자동 실행]
    매일 오전 9시 자동 실행은 install_task_scheduler.bat 으로 Windows 작업 스케줄러에
    등록한다. (이 스크립트 자체에는 스케줄링 로직이 없음 — OS 스케줄러가 매일 이 파일을 실행)

====================================================================
[지금 사용자(=이 파일을 실행/관리하는 분)가 직접 해야 하는 일 — 체크리스트]
====================================================================
    ① (최초 1회) News 폴더(이 파일이 있는 실행파일 폴더의 바로 위 폴더)에서 명령
       프롬프트를 열고
           pip install -r requirements.txt
       를 실행해 필요한 패키지(kiwipiepy, wordcloud, matplotlib, beautifulsoup4,
       requests, lxml)를 설치한다. (requirements.txt가 News 폴더 최상단에 있음
       — 이 파일이 있는 실행파일 폴더가 아니라 그 상위 폴더에서 실행해야 한다)

    ② (최초 1회, 필수) 이 파일이 있는 실행파일 폴더에서 아래 명령으로 실제 기사가
       정상 수집되는지 직접 눈으로 확인한다.
           python News_analytics.py --debug --press 조선일보 --category 경제
       - 콘솔에 "[조선일보/경제] 기사 N건 수집"이 뜨면 정상.
       - "기사 0건" 경고가 뜨면 News/_debug/ 폴더에 저장된 원본 HTML을 확인하고,
         그 파일(또는 콘솔 로그)을 Claude에게 공유하면 선택자를 바로 고쳐준다.
       - 이 스크립트는 개발 환경(Claude 샌드박스)에서 naver.com 접속이 차단되어 있어
         라이브 크롤링을 직접 검증하지 못한 상태로 작성되었다. 형태소 분석·차트·
         워드클라우드·CSV 저장 파이프라인은 샘플 데이터로 정상 동작을 확인했지만,
         실제 네이버 페이지 HTML 구조(선택자)는 이 확인을 거쳐야 확실해진다.

    ③ (선택) 매일 자동 실행이 필요하면 News\\실행파일\\install_task_scheduler.bat 을
       더블클릭한다 (Windows 작업 스케줄러에 매일 09:00 실행 작업이 등록된다).
       자동 실행이 필요 없다면 이 단계는 생략해도 되고, 그때그때 위 ②의 명령이나
       run_test.bat / python News_analytics.py 를 수동으로 실행하면 된다.

    ④ News 폴더 최상단의 ChromeSetup.exe 는 이 스크립트와 무관하다 — 이 파이프라인은
       requests + BeautifulSoup(HTML 직접 파싱) 방식으로 동작하며 브라우저(Chrome)를
       실행하거나 제어하지 않는다. 따라서 ChromeSetup.exe 가 자동으로 실행되지 않는
       것은 정상이며, 그대로 두어도 실행에 아무 영향이 없다(다른 용도로 받아둔
       설치 파일이면 삭제해도 무방하다).

작성: Claude (Cowork) / 최초 작성일: 2026-08-31
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ====================================================================
# 0. 경로 / 기본 설정  (hwp 원본 문서에 명시된 경로를 그대로 사용)
# ====================================================================

# News 프로젝트 루트를 기준으로 폰트/캐시/로그/출력 파일 경로를 잡는다.
# 원래는 "이 스크립트 파일이 위치한 폴더 = News 루트"였지만, 현재는 News_analytics.py와
# install_task_scheduler.bat 을 News\실행파일\ 하위 폴더에 따로 모아두신 상태다.
# 반면 NanumGothic.ttf, requirements.txt, insight_master.csv 등은 News\ 최상단에 있으므로,
# 스크립트가 "실행파일" 폴더 안에서 실행되는 경우에는 그 상위 폴더(News 루트)를 기준으로
# 삼는다. (그래야 폰트를 못 찾아 글자가 깨지거나, 결과물이 News\실행파일\2026\... 처럼
# 엉뚱한 곳에 쌓이는 문제가 생기지 않는다.)
_SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "실행파일" else _SCRIPT_DIR

FONT_PATH = BASE_DIR / "NanumGothic.ttf"          # 워드클라우드/차트용 한글 폰트 (이미 폴더에 존재)
CACHE_DIR = BASE_DIR / "_cache"                    # 언론사 oid 캐시 등
DEBUG_DIR = BASE_DIR / "_debug"                    # 파싱 실패 시 원본 HTML 저장
LOG_DIR = BASE_DIR / "logs"
MASTER_CSV = BASE_DIR / "insight_master.csv"       # 전체 통합 인사이트 CSV (대시보드용)

# ---- 분석 대상 언론사 -------------------------------------------------
# hwp 원본 대상: 매일신문, 문화일보, 조선일보 등 + 확장 대상: 데일리안, 아시아경제
# 자유롭게 추가/삭제 가능. 언론사 고유번호(oid)는 실행 시 자동으로 조회한다.
#
# 주의: 여기 적는 이름은 네이버 뉴스 제휴 언론사 목록(87곳)의 표기와 정확히 같아야
#       한다. 예전에 "매일일보"로 적혀 있었으나 네이버 제휴사가 아니어서 oid 조회에
#       실패했고, 그 언론사만 결과가 통째로 비어 있었다. 실제 등재명은 "매일신문"(088).
#       이름을 못 찾으면 실행 로그에 비슷한 이름 후보를 함께 출력한다.
PRESS_LIST = ["조선일보", "문화일보", "매일신문", "데일리안", "아시아경제"]

# 자동 조회(get_press_oid_map)가 실패할 경우를 대비한 수동 지정용 표.
# 확인된 값이 있으면 여기에 채워 넣으면 우선 사용된다. 예) "조선일보": "023"
PRESS_OID_FALLBACK: dict[str, str] = {
    # "조선일보": "023",
}

# ---- 분석 대상 카테고리(분야) -----------------------------------------
# hwp 원본의 "주요뉴스, 이슈, 경제, 사회, 문화"에 정치/세계/IT·과학을 추가해
# 8개 카테고리 전체를 분석 대상으로 삼는다.
# sid 는 네이버 뉴스 언론사 홈(media.naver.com/press/{oid}) 표준 섹션 코드.
#   100=정치, 101=경제, 102=사회, 103=생활/문화, 104=세계, 105=IT/과학
# 주의 1: 파라미터 이름은 sid1 이 아니라 sid 다. ?sid1= 을 쓰면 네이버가 그 값을
#         무시하고 언론사 홈과 같은 목록을 돌려주기 때문에, 모든 카테고리가 똑같은
#         기사로 분석되는 문제가 생긴다(실측 확인).
# 주의 2: "IT/과학" 키에는 '/'를 넣지 않는다 — 이 값이 그대로 저장 폴더명으로 쓰이는데,
#         경로에 '/'가 섞이면 의도치 않게 하위 폴더(IT/과학 두 단계)가 생기기 때문이다.
CATEGORIES: dict[str, dict] = {
    "주요뉴스": {"path": "",          "sid": None},   # 언론사 홈(전체) 헤드라인
    "이슈":     {"path": "/ranking",  "sid": None},   # 언론사별 많이 본 뉴스(랭킹) - 이슈 대용
    "정치":     {"path": "",          "sid": "100"},
    "경제":     {"path": "",          "sid": "101"},
    "사회":     {"path": "",          "sid": "102"},
    "문화":     {"path": "",          "sid": "103"},
    "세계":     {"path": "",          "sid": "104"},
    "IT과학":   {"path": "",          "sid": "105"},
}

TOP_N_NOUNS = 100        # 명사 상위 추출 개수 (언론사 x 카테고리 1건 기준)
TOP_N_CHART = 20         # 빈도수 바 차트에 표시할 상위 개수 (요구사항: 상위 20개)

# ---- 일 단위 종합(전 언론사 x 전 카테고리 합산) 설정 --------------------
# 하루치 결과를 모두 더한 Counter 로 그리므로 개별 조합보다 빈도수가 크게 올라간다.
# 그만큼 워드클라우드에 실을 단어 수도 늘려 잡는다.
TOP_N_NOUNS_DAILY = 200      # 일간 종합 워드클라우드에 표시할 단어 수
TOP_N_CHART_DAILY = 20       # 일간 종합 빈도수 바 차트 상위 개수 (개별과 동일)
TOP_N_SENTIMENT_CHART = 10   # 감성 바 차트: 긍정 10개 + 부정 10개 = 총 20개

# ---- 감성 시각화 색상 (진한 색 = 빈도 1위, 옅은 색 = 하위) ---------------
POS_COLOR_DARK = "#0D2B5C"   # 긍정: 진한 남청색
POS_COLOR_LIGHT = "#A8D0F0"  # 긍정: 옅은 청색
NEG_COLOR_DARK = "#7A0A12"   # 부정: 진한 빨강
NEG_COLOR_LIGHT = "#F2A6A6"  # 부정: 옅은 빨강
NEUTRAL_COLOR = "#9E9E9E"    # 감성 사전에 없는 단어(감성 그래프에서는 쓰이지 않음)

# 워드클라우드 글자 크기 상한.
# 감성 워드클라우드는 사전에 걸린 단어만 남아 단어 수가 적어질 수 있는데,
# 상한이 없으면 몇 글자가 캔버스를 가득 채워 읽기 어려워진다.
WORDCLOUD_MAX_FONT_SIZE = 170
WORDCLOUD_MIN_FONT_SIZE = 10

# ---- 그래프 제목 규칙 ---------------------------------------------------
# 모든 이미지 상단 제목은 [날짜 - (신문사/종합) - 카테고리 - 분석 유형] 형식으로 통일한다.
TITLE_SCOPE_DAILY = "종합"          # 일간 종합 그래프의 신문사 자리 표기
TITLE_CATEGORY_DAILY = "전체 카테고리"  # 일간 종합 그래프의 카테고리 자리 표기
MAX_ARTICLES_PER_PAGE = 40   # 카테고리 페이지당 최대 수집 기사 수 (과도한 요청 방지)
REQUEST_TIMEOUT = 10
REQUEST_DELAY_SEC = 0.6   # 목록 페이지 요청 사이 지연(네이버 서버 부담 최소화 - 예의상 딜레이)

# ---- 기사 본문 수집(키워드 분석에 제목뿐 아니라 본문까지 반영) -----------
FETCH_FULL_TEXT_DEFAULT = True   # True: 기사 상세 페이지(#dic_area) 본문까지 가져와 분석에 반영
MAX_ARTICLES_FOR_TEXT = 15       # 카테고리당 본문을 가져올 최대 기사 수(요청 수 제한, 나머지는 제목만 사용)
ARTICLE_REQUEST_DELAY_SEC = 0.4  # 본문 요청 사이 지연(초)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# 명사 추출 시 제외할 뉴스 클리셰(상투어)/불용어
# - 실제 이슈 키워드가 아닌, 기사 형식상 반복적으로 등장하는 단어들을 걸러내기 위한 목록.
#   필요에 따라 자유롭게 추가/삭제해서 사용하세요.
STOPWORDS = {
    # 보도 형식/저작권 관련
    "기자", "사진", "뉴스", "종합", "속보", "단독", "영상", "취재", "인터뷰",
    "브리핑", "보도", "특파원", "제공", "무단", "전재", "재배포", "저작권",
    "구독", "댓글", "네이버", "기사",
    # 시간 표현
    "오늘", "내일", "어제", "이번", "지난", "오전", "오후", "이날", "당시",
    "이후", "이전", "동안", "최근", "현재", "앞서", "다음", "지난해", "올해",
    "내년", "작년", "이달", "이번주", "이번달", "당일", "연일", "매일",
    # 보도체 상투 표현 (발언 인용, 전개 서술 등)
    "발표", "밝혔", "전했", "말했", "강조", "설명", "예상", "전망", "계획",
    "마련", "진행", "예정", "시작", "마무리", "등장", "지적", "언급", "밝혀",
    "나타났", "이어졌", "알려졌", "확인됐", "분석됐", "조사됐", "발생",
    # 추상적 범용 명사 (특정 이슈를 나타내지 않는 단어)
    "때문", "정도", "경우", "한편", "특히", "그것", "그동안", "우리", "저희",
    "부분", "자리", "활동", "노력", "필요", "문제", "상태", "상황", "이유",
    "결과", "이상", "이하", "여부", "형태", "가운데", "모습", "생각", "사실",
    "관련", "가장", "위해", "통해", "대한", "관계자", "사람", "모든", "하나",
}

# ---- 감성 사전 (명사 기준) ---------------------------------------------
# extract_noun_counter() 가 만든 "불용어가 제거된 명사 Counter" 를 그대로 재사용해
# 감성을 분류한다. 별도의 재수집·재파싱 없이 전처리 결과만 쓰는 구조라
# 추가 네트워크 요청이 발생하지 않는다.
# 사전에 없는 단어는 중립으로 보고 감성 그래프에서 제외한다.
# 단어를 추가/삭제하면 감성 바 차트와 감성 워드클라우드 양쪽에 즉시 반영된다.
POSITIVE_WORDS = {
    # 실적/지표 개선
    "성장", "증가", "상승", "확대", "개선", "회복", "호조", "호황", "흑자",
    "최대", "최고", "신기록", "돌파", "급등", "강세", "반등", "활성화", "증진",
    "향상", "강화", "순항", "청신호", "선방", "성장세", "상향", "증대", "풍년",
    "부양", "완판", "훈풍",
    # 성과/평가
    "성공", "성과", "달성", "수상", "선정", "우수", "우량", "인기", "호평",
    "찬사", "환영", "승리", "우승", "선두", "혁신", "도약", "진전", "흥행",
    "주목", "기대", "낙관", "희망", "자신감", "명작", "수작",
    # 관계/해결
    "합의", "타결", "협력", "상생", "화해", "협약", "동맹", "지원", "혜택",
    "수혜", "해소", "완화", "절감", "안정", "안전", "신뢰", "효율", "만족",
    "구제", "치유", "완치", "개통", "출시", "유치", "투자", "기부", "나눔",
    "봉사", "응원", "축하", "활력", "화합", "상승세", "우호", "친선", "평화",
    "소통", "배려", "포용",
    # 사업/고용
    "계약", "체결", "수주", "확보", "참여", "개최", "개막", "준공", "완공",
    "취업", "채용", "고용", "창출", "신설", "증설", "확충", "신제품", "특허",
    "신기술", "순이익", "배당", "상장", "흑자전환", "최다", "우대", "절약",
    "편의", "활황", "열풍", "대박",
    # 인정/수상
    "인정", "승격", "합격", "당선", "가결", "통과", "표창", "훈장", "장학",
    "후원", "기증", "감사", "격려", "최우수", "금메달", "쾌거", "낭보",
    # 문화/사회
    "축제", "공연", "전시", "화제", "감동", "구출", "생환", "무사", "호전",
    "회복세",
}

NEGATIVE_WORDS = {
    # 실적/지표 악화
    "하락", "감소", "축소", "침체", "부진", "악화", "적자", "손실", "폭락",
    "급락", "약세", "둔화", "불황", "미달", "역성장", "하향", "후퇴", "적신호",
    "부채", "연체", "파산", "도산", "부도", "실업", "해고", "감원", "격차",
    "하락세", "하방", "경색",
    # 사건/사고
    "사고", "참사", "재난", "피해", "붕괴", "화재", "폭발", "부상", "사망",
    "감염", "확진", "오염", "실종", "침수", "가뭄", "폭염", "한파", "지진",
    "산불", "누출",
    # 범죄/수사
    "범죄", "폭행", "살인", "사기", "비리", "부패", "횡령", "배임", "뇌물",
    "혐의", "수사", "압수", "고발", "기소", "구속", "체포", "소송", "재판",
    "불법", "위반", "제재", "과징금", "벌금", "처벌", "적발", "은폐", "담합",
    # 갈등/정치
    "위기", "우려", "불안", "위험", "논란", "갈등", "대립", "충돌", "반발",
    "비판", "항의", "시위", "파업", "공방", "의혹", "논쟁", "마찰", "보복",
    "압박", "규제", "제한", "사퇴", "경질", "해임", "탄핵", "패배", "최악",
    # 실패/중단
    "실패", "무산", "지연", "차질", "결함", "리콜", "취소", "중단", "폐지",
    "부작용", "혼란", "공포", "퇴출", "철회", "반려", "좌초", "결렬", "파행",
    "난항", "표류", "부실", "미흡", "위축", "부담", "경고", "비상",
    # 폭력/강력범죄
    "흉기", "살해", "자살", "자폭", "폭력", "협박", "위협", "테러", "전쟁",
    "침공", "공습", "타격", "살상", "시체", "사체", "유기", "방화", "절도",
    "강도", "납치", "감금", "폭언", "학대", "성추행", "성폭행", "마약", "도박",
    "밀수", "탈세", "체납", "갑질", "차별", "혐오",
    # 사법/처벌
    "반대", "부결", "거부", "폐기", "유출", "유죄", "징역", "실형", "피의자",
    "사상자", "허위", "조작", "왜곡", "위조", "표절", "유착", "청탁", "비난",
    "규탄", "성토", "파괴", "훼손", "손괴", "손상",
}


# ====================================================================
# 1. 로깅
# ====================================================================

def setup_logging(debug: bool = False) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{datetime.now():%Y-%m-%d}.log"

    logger = logging.getLogger("news_analytics")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


log = logging.getLogger("news_analytics")


# ====================================================================
# 2. 언론사 oid(고유번호) 조회
# ====================================================================

def get_press_oid_map(force_refresh: bool = False) -> dict[str, str]:
    """네이버 뉴스 '언론사 목록' 페이지에서 (언론사명 -> oid) 매핑을 조회하고 캐시한다.

    캐시 파일: News/_cache/press_oid_map.json (30일간 재사용)
    조회에 실패하면 PRESS_OID_FALLBACK 값을 사용하도록 빈 dict를 반환한다.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "press_oid_map.json"

    if not force_refresh and cache_file.exists():
        age_days = (time.time() - cache_file.stat().st_mtime) / 86400
        if age_days < 30:
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    mapping: dict[str, str] = {}
    try:
        resp = requests.get(
            "https://news.naver.com/main/officeList.naver",
            headers=HEADERS, timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.find_all("a", href=True):
            m = re.search(r"oid=(\d{2,4})", a["href"])
            if not m:
                continue
            name = a.get_text(strip=True)
            if name:
                mapping[name] = m.group(1)
        log.info("언론사 목록 조회 성공: %d개 언론사 확인", len(mapping))
    except Exception as e:
        log.warning("언론사 목록 자동 조회 실패 (%s) - PRESS_OID_FALLBACK 값을 사용합니다.", e)

    if mapping:
        cache_file.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    return mapping


def resolve_oid(press_name: str, oid_map: dict[str, str]) -> Optional[str]:
    if press_name in PRESS_OID_FALLBACK:
        return PRESS_OID_FALLBACK[press_name]
    if press_name in oid_map:
        return oid_map[press_name]
    # 부분 일치 시도 (예: "조선일보" vs "조선일보TV" 등 표기 차이 대응)
    for name, oid in oid_map.items():
        if press_name in name or name in press_name:
            return oid
    return None


# ====================================================================
# 3. 기사 수집
# ====================================================================

@dataclass
class Article:
    title: str
    url: str


def _save_debug_html(html: str, press: str, category: str) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    fname = DEBUG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{press}_{category}.html"
    fname.write_text(html, encoding="utf-8")
    log.debug("디버그 HTML 저장: %s", fname)


def fetch_html(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log.warning("페이지 요청 실패: %s (%s)", url, e)
        return None


def fetch_article_text(url: str) -> str:
    """기사 상세 페이지에서 본문 텍스트를 가져온다.

    네이버 뉴스 기사 본문은 `#dic_area` 요소 안에 들어 있다. 이 함수가 반환한 텍스트는
    process_one()에서 기사 제목과 함께 extract_noun_counter()에 전달되어, 제목만이
    아니라 본문 내용까지 키워드 분석에 반영되도록 한다.

    본문을 가져오지 못하면(요청 실패, 페이지 구조 변경 등) 빈 문자열을 반환한다 —
    상위 호출부는 이 경우 해당 기사의 제목만으로 분석을 이어가며 전체 파이프라인이
    멈추지 않는다.
    """
    html = fetch_html(url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")
    body = soup.select_one("#dic_area")
    if body is None:
        log.debug("본문 선택자(#dic_area)를 찾지 못함: %s", url)
        return ""

    # 스크립트/스타일 등 본문 텍스트가 아닌 하위 요소는 제외하고 순수 텍스트만 추출
    for tag in body.select("script, style"):
        tag.decompose()

    return body.get_text(separator=" ", strip=True)


# 목록 페이지에서 제목 끝에 따라붙는 상대 시각 표기('5분전', '1시간전' 등).
# 떼어내지 않으면 '시간', '분' 같은 단어가 키워드 상위권에 올라온다.
_TIME_SUFFIX_RE = re.compile(r"\s*(?:\d+\s*(?:초|분|시간|일)\s*전|어제|오늘)$")


def _clean_title(raw_title: str, category: str, rank: int) -> str:
    """목록 페이지에서 제목에 딸려오는 군더더기를 제거한다.

    - 섹션 목록: 제목 끝에 '5분전', '1시간전' 같은 상대 시각이 붙는다.
    - 랭킹(이슈) 목록: 제목 앞에 순위 숫자가 붙는다. 다만 '8월 반도체 수출...'처럼
      숫자로 시작하는 정상 제목을 훼손하면 안 되므로, **그 항목의 순위와 정확히
      일치하는 숫자**로 시작할 때만 떼어낸다.
    """
    title = raw_title
    if category == "이슈":
        prefix = str(rank)
        rest = title[len(prefix):]
        if title.startswith(prefix) and not rest[:1].isdigit():
            title = rest
    return _TIME_SUFFIX_RE.sub("", title).strip()


def collect_articles(oid: str, press: str, category: str, debug: bool = False) -> list[Article]:
    """언론사(oid) × 카테고리 페이지에서 기사 제목/링크 목록을 수집한다.

    네이버 기사 링크는 항상 `article/{oid}/{aid}` 패턴을 포함하므로, 이 패턴을 가진
    <a> 태그를 모두 찾아 제목(텍스트)과 함께 추출하는 방식으로 페이지 구조 변경에
    최대한 견고하게 대응한다.

    링크에서 뽑은 oid 가 대상 언론사와 다르면 버린다. 목록 하단의 추천/관련 기사
    영역에 다른 언론사 기사가 섞여 들어와 언론사별 분석을 오염시키기 때문이다.
    """
    cfg = CATEGORIES[category]
    if cfg["sid"]:
        url = f"https://media.naver.com/press/{oid}?sid={cfg['sid']}"
    else:
        url = f"https://media.naver.com/press/{oid}{cfg['path']}"

    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    seen_urls: set[str] = set()
    articles: list[Article] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        matched = re.search(r"/article/(\d+)/\d+", href)
        if not matched:
            continue
        if matched.group(1) != oid:
            continue          # 다른 언론사 기사(추천/관련 영역)는 제외
        if href.startswith("/"):
            href = "https://n.news.naver.com" + href
        if href in seen_urls:
            continue
        title = _clean_title(a.get_text(strip=True), category, len(articles) + 1)
        if not title or len(title) < 4:
            continue
        seen_urls.add(href)
        articles.append(Article(title=title, url=href))
        if len(articles) >= MAX_ARTICLES_PER_PAGE:
            break

    if not articles:
        log.warning("[%s/%s] 수집된 기사 0건 - 페이지 구조가 다를 수 있습니다. (url=%s)", press, category, url)
        if debug:
            _save_debug_html(html, press, category)
    else:
        log.info("[%s/%s] 기사 %d건 수집", press, category, len(articles))

    return articles


# ====================================================================
# 4. 명사 추출 / 빈도 분석
# ====================================================================

_kiwi = None


def get_kiwi():
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi
        _kiwi = Kiwi()
    return _kiwi


def extract_noun_counter(texts: list[str], top_n: int = TOP_N_NOUNS) -> Counter:
    kiwi = get_kiwi()
    counter: Counter = Counter()
    for text in texts:
        for token in kiwi.tokenize(text):
            if token.tag not in ("NNG", "NNP"):
                continue
            word = token.form
            if len(word) < 2 or word in STOPWORDS:
                continue
            counter[word] += 1
    # 상위 top_n 개만 남긴다
    return Counter(dict(counter.most_common(top_n)))


# ====================================================================
# 5. 시각화 (막대그래프 / 워드클라우드)
# ====================================================================

def make_title(date_str: str, scope: str, category: str, kind: str) -> str:
    """모든 그래프 제목을 [날짜 - (신문사/종합) - 카테고리 - 분석 유형] 형식으로 통일한다.

    예) 2026-09-01 - 조선일보 - 경제 - 빈도수 워드클라우드
        2026-09-01 - 종합 - 전체 카테고리 - 감성분석 바차트
    """
    return f"{date_str} - {scope} - {category} - {kind}"


def _load_font():
    """한글 폰트 FontProperties 를 돌려준다(폰트 파일이 없으면 None)."""
    from matplotlib import font_manager
    return font_manager.FontProperties(fname=str(FONT_PATH)) if FONT_PATH.exists() else None


def _gradient_colors(dark_hex: str, light_hex: str, n: int) -> list[str]:
    """진한 색 -> 옅은 색으로 이어지는 색 n개를 만든다(0번이 가장 진한 색).

    "빈도 1위 = 가장 진한 색, 순위가 내려갈수록 옅은 색" 규칙을 감성 바 차트와
    감성 워드클라우드에 동일하게 적용하기 위한 공통 함수.
    """
    from matplotlib.colors import LinearSegmentedColormap, to_hex

    if n <= 0:
        return []
    cmap = LinearSegmentedColormap.from_list("sentiment", [dark_hex, light_hex])
    if n == 1:
        return [to_hex(cmap(0.0))]
    return [to_hex(cmap(i / (n - 1))) for i in range(n)]


def save_bar_chart(counter: Counter, out_path: Path, title: str,
                    top_n: int = TOP_N_CHART) -> None:
    # counter는 extract_noun_counter()에서 이미 STOPWORDS(불용어) 제거를 마친
    # 결과이므로, 여기서 별도의 전처리 없이 바로 시각화에 사용한다.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    top_items = counter.most_common(top_n)
    if not top_items:
        log.warning("빈도수 바 차트 생략(데이터 없음): %s", out_path)
        return

    fp = _load_font()
    labels = [w for w, _ in top_items][::-1]
    values = [c for _, c in top_items][::-1]

    fig, ax = plt.subplots(figsize=(9.5, max(5.5, 0.40 * len(labels) + 1.8)))
    bars = ax.barh(labels, values, color="#2E86AB")
    ax.set_title(title, fontproperties=fp, fontsize=15, pad=12)
    ax.set_xlabel("빈도수", fontproperties=fp, fontsize=11)
    if fp:
        for label in ax.get_yticklabels():
            label.set_fontproperties(fp)
            label.set_fontsize(11)
    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                 str(value), va="center", fontsize=9)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def save_wordcloud(counter: Counter, out_path: Path, title: str,
                    max_words: int = TOP_N_NOUNS) -> None:
    # counter는 extract_noun_counter()에서 이미 STOPWORDS(불용어) 제거를 마친
    # 결과이므로, 워드클라우드에도 불용어 제거가 동일하게 반영되어 있다.
    # WordCloud 이미지 자체에는 제목을 넣을 수 없으므로 matplotlib 캔버스에 얹어
    # 제목을 붙인 뒤 저장한다(모든 이미지 파일에 제목을 넣기 위함).
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    if not counter:
        log.warning("워드클라우드 생략(데이터 없음): %s", out_path)
        return

    wc = WordCloud(
        font_path=str(FONT_PATH) if FONT_PATH.exists() else None,
        background_color="white",
        width=1000, height=700,
        max_words=max_words,
        max_font_size=WORDCLOUD_MAX_FONT_SIZE,
        min_font_size=WORDCLOUD_MIN_FONT_SIZE,
        colormap="viridis",
    ).generate_from_frequencies(counter)

    fp = _load_font()
    fig, ax = plt.subplots(figsize=(10, 7.6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontproperties=fp, fontsize=15, pad=14)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


# ====================================================================
# 5-1. 감성 분석 (전처리 결과인 명사 Counter 를 그대로 재사용)
# ====================================================================

def split_sentiment(counter: Counter) -> tuple[Counter, Counter]:
    """명사 Counter 를 긍정/부정 Counter 로 나눈다(사전에 없으면 중립 = 제외)."""
    positive = Counter({w: c for w, c in counter.items() if w in POSITIVE_WORDS})
    negative = Counter({w: c for w, c in counter.items() if w in NEGATIVE_WORDS})
    return positive, negative


def save_sentiment_bar_chart(positive: Counter, negative: Counter, out_path: Path,
                              title: str, top_n: int = TOP_N_SENTIMENT_CHART) -> None:
    """긍정 Top10 + 부정 Top10 = 총 20개를 하나의 차트에 양방향으로 배치한다.

    오른쪽(긍정)은 진한 남청색 -> 옅은 청색, 왼쪽(부정)은 진한 빨강 -> 옅은 빨강.
    각 그룹 안에서 빈도 1위가 가장 진한 색이 된다.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from matplotlib.ticker import FuncFormatter

    pos_items = positive.most_common(top_n)
    neg_items = negative.most_common(top_n)
    if not pos_items and not neg_items:
        log.warning("감성 바 차트 생략(감성 사전에 걸린 단어 없음): %s", out_path)
        return

    fp = _load_font()
    pos_colors = _gradient_colors(POS_COLOR_DARK, POS_COLOR_LIGHT, len(pos_items))
    neg_colors = _gradient_colors(NEG_COLOR_DARK, NEG_COLOR_LIGHT, len(neg_items))

    # 위에서부터 긍정 상위 -> 부정 상위 순으로 놓는다(barh 는 아래가 0번이므로 뒤집는다).
    labels = [w for w, _ in pos_items] + [w for w, _ in neg_items]
    values = [c for _, c in pos_items] + [-c for _, c in neg_items]
    colors = pos_colors + neg_colors
    labels, values, colors = labels[::-1], values[::-1], colors[::-1]

    ypos = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(10, max(6.0, 0.40 * len(labels) + 2.0)))
    bars = ax.barh(ypos, values, color=colors)

    ax.axvline(0, color="#444444", linewidth=0.9)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    if fp:
        for label in ax.get_yticklabels():
            label.set_fontproperties(fp)
            label.set_fontsize(11)

    span = max(abs(v) for v in values)
    for bar, value in zip(bars, values):
        offset = span * 0.015
        x = bar.get_width() + (offset if value >= 0 else -offset)
        ax.text(x, bar.get_y() + bar.get_height() / 2, str(abs(value)),
                 va="center", ha="left" if value >= 0 else "right", fontsize=9)

    ax.set_xlim(-span * 1.20, span * 1.20)
    # x축은 좌우 모두 "빈도수"이므로 음수 부호 없이 절댓값으로 표기한다.
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: str(abs(int(v)))))
    ax.set_xlabel("빈도수  (왼쪽 = 부정 / 오른쪽 = 긍정)", fontproperties=fp, fontsize=11)
    ax.set_title(title, fontproperties=fp, fontsize=15, pad=12)

    handles = [
        Patch(facecolor=POS_COLOR_DARK, label=f"긍정 Top {len(pos_items)} (진한 남청색 = 상위)"),
        Patch(facecolor=NEG_COLOR_DARK, label=f"부정 Top {len(neg_items)} (진한 빨강 = 상위)"),
    ]
    ax.legend(handles=handles, prop=fp, loc="lower right", fontsize=9, framealpha=0.9)

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def save_sentiment_wordcloud(positive: Counter, negative: Counter, out_path: Path,
                              title: str, max_words: int = TOP_N_NOUNS) -> None:
    """긍정어와 부정어를 색상으로 구별해 하나의 워드클라우드로 그린다.

    바 차트와 같은 규칙(빈도 1위 = 가장 진한 색)을 그대로 적용한다.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from wordcloud import WordCloud

    combined: Counter = Counter()
    combined.update(positive)
    combined.update(negative)
    if not combined:
        log.warning("감성 워드클라우드 생략(감성 사전에 걸린 단어 없음): %s", out_path)
        return

    pos_rank = {w: i for i, (w, _) in enumerate(positive.most_common())}
    neg_rank = {w: i for i, (w, _) in enumerate(negative.most_common())}
    pos_colors = _gradient_colors(POS_COLOR_DARK, POS_COLOR_LIGHT, max(1, len(pos_rank)))
    neg_colors = _gradient_colors(NEG_COLOR_DARK, NEG_COLOR_LIGHT, max(1, len(neg_rank)))

    def color_func(word, **kwargs):
        if word in pos_rank:
            return pos_colors[pos_rank[word]]
        if word in neg_rank:
            return neg_colors[neg_rank[word]]
        return NEUTRAL_COLOR

    wc = WordCloud(
        font_path=str(FONT_PATH) if FONT_PATH.exists() else None,
        background_color="white",
        width=1000, height=700,
        max_words=max_words,
        max_font_size=WORDCLOUD_MAX_FONT_SIZE,
        min_font_size=WORDCLOUD_MIN_FONT_SIZE,
        color_func=color_func,
    ).generate_from_frequencies(combined)

    fp = _load_font()
    fig, ax = plt.subplots(figsize=(10, 8.0))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontproperties=fp, fontsize=15, pad=14)
    # 범례를 그림 위에 얹으면 단어를 가리므로 캔버스 아래쪽 바깥에 배치한다.
    handles = [
        Patch(facecolor=POS_COLOR_DARK, label=f"긍정 {len(pos_rank)}종 (진한 남청색 = 빈도 상위)"),
        Patch(facecolor=NEG_COLOR_DARK, label=f"부정 {len(neg_rank)}종 (진한 빨강 = 빈도 상위)"),
    ]
    ax.legend(handles=handles, prop=fp, loc="upper center",
               bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=10, frameon=False)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


# ====================================================================
# 5-2. 그래프 4종 일괄 생성 (개별 / 일간 종합 공통)
# ====================================================================

def save_counter_csv(counter: Counter, out_path: Path, date_str: str,
                      scope: str, category: str) -> None:
    """정규화(명사 추출) + 불용어 제거가 끝난 분석 결과를 그대로 CSV로 남긴다.

    그래프에 쓰인 것과 완전히 같은 Counter 를 기록하므로, 그림에서 읽은 값과
    CSV 값이 항상 일치한다. 컬럼은 다음과 같다.

        날짜 / 구분(신문사 또는 "종합") / 카테고리 / 순위 / 단어 / 빈도수 / 감성

    감성은 POSITIVE_WORDS / NEGATIVE_WORDS 사전 기준이며, 사전에 없으면 "중립".
    인사이트 CSV(insight_master.csv)가 누적(append) 방식인 것과 달리 이 파일은
    같은 날 다시 실행하면 덮어쓴다 — 그날의 최종 분석 결과 하나만 남기기 위함이다.
    """
    if not counter:
        log.warning("키워드 빈도 CSV 생략(데이터 없음): %s", out_path)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["날짜", "구분", "카테고리", "순위", "단어", "빈도수", "감성"])
        for rank, (word, freq) in enumerate(counter.most_common(), start=1):
            if word in POSITIVE_WORDS:
                sentiment = "긍정"
            elif word in NEGATIVE_WORDS:
                sentiment = "부정"
            else:
                sentiment = "중립"
            writer.writerow([date_str, scope, category, rank, word, freq, sentiment])

    log.info("키워드 빈도 CSV 저장: %s (%d단어)", out_path.name, len(counter))


def save_sentiment_csv(positive: Counter, negative: Counter, out_path: Path,
                        date_str: str, scope: str, category: str,
                        top_n: int = TOP_N_SENTIMENT_CHART) -> None:
    """감성 그래프(③④)를 그리는 데 실제로 쓰인 기초 자료를 CSV로 남긴다.

    감성 사전에 걸린 단어만 대상이며(중립어는 제외 — 중립까지 포함된 전체 목록은
    `..._키워드빈도_*.csv` 에 있다), 그래프에 칠해진 색상 값까지 그대로 기록해
    그림과 표를 1:1로 대조할 수 있게 했다.

    컬럼
        날짜 / 구분 / 카테고리 / 감성 / 순위 / 단어 / 빈도수
        감성내비중(%)   - 같은 감성 그룹 안에서 그 단어가 차지하는 빈도 비중
        감성단어수      - 그 감성 그룹의 단어 종수
        감성총빈도      - 그 감성 그룹의 빈도 합계
        워드클라우드_색상 - 감성 워드클라우드에 칠해진 색(그룹 전체 기준 그라데이션)
        바차트_색상       - 감성 바 차트에 칠해진 색(Top N 기준 그라데이션, 미표시는 공란)
        바차트표시        - 감성 바 차트에 나왔으면 Y, 아니면 N

    워드클라우드는 그룹 전체에, 바 차트는 표시되는 Top N 에 각각 그라데이션을
    펼치기 때문에 같은 단어라도 두 그래프의 색이 다를 수 있다. 두 값을 모두
    남기는 이유다. 어느 쪽이든 "빈도 1위 = 가장 진한 색" 규칙은 동일하다.
    """
    if not positive and not negative:
        log.warning("감성 기초자료 CSV 생략(감성 사전에 걸린 단어 없음): %s", out_path)
        return

    rows = []
    for label, group in (("긍정", positive), ("부정", negative)):
        items = group.most_common()
        if not items:
            continue
        dark, light = ((POS_COLOR_DARK, POS_COLOR_LIGHT) if label == "긍정"
                        else (NEG_COLOR_DARK, NEG_COLOR_LIGHT))
        wc_colors = _gradient_colors(dark, light, len(items))
        bar_colors = _gradient_colors(dark, light, min(top_n, len(items)))
        total = sum(c for _, c in items)

        for rank, (word, freq) in enumerate(items, start=1):
            in_chart = rank <= top_n
            rows.append([
                date_str, scope, category, label, rank, word, freq,
                round(freq / total * 100, 2) if total else 0.0,
                len(items), total,
                wc_colors[rank - 1],
                bar_colors[rank - 1] if in_chart else "",
                "Y" if in_chart else "N",
            ])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "날짜", "구분", "카테고리", "감성", "순위", "단어", "빈도수",
            "감성내비중(%)", "감성단어수", "감성총빈도",
            "워드클라우드_색상", "바차트_색상", "바차트표시",
        ])
        writer.writerows(rows)

    log.info("감성 기초자료 CSV 저장: %s (긍정 %d종 / 부정 %d종)",
              out_path.name, len(positive), len(negative))


def save_graph_set(counter: Counter, out_dir: Path, name_prefix: str, ymd: str,
                    date_str: str, scope: str, category: str,
                    top_n_chart: int = TOP_N_CHART,
                    max_words: int = TOP_N_NOUNS) -> None:
    """요구사항의 그래프 4종을 한 번에 만든다.

        (1) 빈도수 워드클라우드      - 단어 전체 빈도수 기반
        (2) 빈도수 바 차트           - 상위 top_n_chart 개
        (3) 감성분석 워드클라우드    - 긍정/부정을 색으로 구별
        (4) 감성분석 바 차트         - 긍정 Top10 + 부정 Top10 = 총 20개

    그래프와 함께 CSV 2종도 저장한다.
        `{name_prefix}_키워드빈도_{ymd}.csv`
            정규화(명사 추출) + 불용어 제거를 마친 전체 단어/빈도/감성 — ①② 원본
        `{name_prefix}_감성분석기초자료_{ymd}.csv`
            감성 사전에 걸린 단어만 추린 감성 그래프 기초 자료 + 색상값 — ③④ 원본

    감성 분석은 인자로 받은 counter(불용어 제거를 마친 전처리 결과)를 그대로
    재사용하므로 추가 수집·재파싱이 없다.
    모든 제목은 [날짜 - (신문사/종합) - 카테고리 - 분석 유형] 형식이다.
    """
    positive, negative = split_sentiment(counter)

    # 그래프의 원본 데이터(정규화 + 불용어 제거를 마친 결과)를 CSV로도 남긴다.
    save_counter_csv(
        counter,
        out_dir / f"{name_prefix}_키워드빈도_{ymd}.csv",
        date_str, scope, category,
    )
    # 감성 그래프(③④)의 기초 자료도 별도 CSV로 남긴다.
    save_sentiment_csv(
        positive, negative,
        out_dir / f"{name_prefix}_감성분석기초자료_{ymd}.csv",
        date_str, scope, category,
    )

    save_wordcloud(
        counter,
        out_dir / f"{name_prefix}_빈도수_wordcloud_{ymd}.png",
        make_title(date_str, scope, category, "빈도수 워드클라우드"),
        max_words=max_words,
    )
    save_bar_chart(
        counter,
        out_dir / f"{name_prefix}_빈도수_barplot_TOP{top_n_chart}_{ymd}.png",
        make_title(date_str, scope, category, f"빈도수 바차트 TOP {top_n_chart}"),
        top_n=top_n_chart,
    )
    save_sentiment_wordcloud(
        positive, negative,
        out_dir / f"{name_prefix}_감성분석_wordcloud_{ymd}.png",
        make_title(date_str, scope, category, "감성분석 워드클라우드"),
        max_words=max_words,
    )
    save_sentiment_bar_chart(
        positive, negative,
        out_dir / f"{name_prefix}_감성분석_barplot_{ymd}.png",
        make_title(date_str, scope, category,
                    f"감성분석 바차트 (긍정 Top {TOP_N_SENTIMENT_CHART} · 부정 Top {TOP_N_SENTIMENT_CHART})"),
    )


def sentiment_stats(counter: Counter) -> dict:
    """Counter 하나에 대한 감성 지표를 계산한다.

    감성지수 = (긍정 총빈도 - 부정 총빈도) / (긍정 + 부정 총빈도) x 100
        +100 에 가까울수록 긍정 우세, -100 에 가까울수록 부정 우세, 0 이면 균형.
    감성어가 하나도 없으면 0.0 으로 둔다.
    """
    positive, negative = split_sentiment(counter)
    pos_total = sum(positive.values())
    neg_total = sum(negative.values())
    denom = pos_total + neg_total
    return {
        "positive": positive,
        "negative": negative,
        "pos_kinds": len(positive),
        "neg_kinds": len(negative),
        "pos_total": pos_total,
        "neg_total": neg_total,
        "index": round((pos_total - neg_total) / denom * 100, 1) if denom else 0.0,
    }


def _top_phrase(counter: Counter, n: int = 5) -> str:
    """'단어(빈도); 단어(빈도)' 형태의 요약 문자열."""
    return "; ".join(f"{w}({c})" for w, c in counter.most_common(n))


def _unit_insight(label: str, counter: Counter, articles: int, stat: dict) -> str:
    """신문사/카테고리 등 한 단위에 대한 규칙 기반 인사이트 한 문장."""
    if not counter:
        return f"{label}: 집계된 키워드가 없습니다."

    top3 = ", ".join(f"'{w}'({c}회)" for w, c in counter.most_common(3))
    if stat["index"] >= 20:
        tone = "긍정 어휘가 뚜렷하게 우세"
    elif stat["index"] >= 5:
        tone = "긍정 어휘가 다소 우세"
    elif stat["index"] > -5:
        tone = "긍정과 부정이 비슷한 수준"
    elif stat["index"] > -20:
        tone = "부정 어휘가 다소 우세"
    else:
        tone = "부정 어휘가 뚜렷하게 우세"

    return (
        f"{label}: 기사 {articles}건에서 키워드 {len(counter)}종을 추출했고 "
        f"상위 키워드는 {top3} 순입니다. "
        f"감성지수 {stat['index']:+.1f}로 {tone}합니다."
    )


def generate_daily_insight_report(daily_counter: Counter, records: list[dict],
                                   date_obj: datetime) -> str:
    """하루치 분석 결과를 항목별로 풀어쓴 상세 인사이트 리포트(여러 줄)를 만든다.

    개별 조합의 한 줄 인사이트(generate_insight)보다 한 단계 위에서,
    신문사 간 비교 / 카테고리 간 비교 / 공통 의제 / 단독 보도까지 함께 정리한다.
    """
    date_str = date_obj.strftime("%Y-%m-%d")

    press_counters: dict[str, Counter] = defaultdict(Counter)
    cat_counters: dict[str, Counter] = defaultdict(Counter)
    press_articles: dict[str, int] = defaultdict(int)
    cat_articles: dict[str, int] = defaultdict(int)
    for r in records:
        press_counters[r["press"]].update(r["counter"])
        cat_counters[r["category"]].update(r["counter"])
        press_articles[r["press"]] += r["articles"]
        cat_articles[r["category"]] += r["articles"]

    total_articles = sum(press_articles.values())
    total_freq = sum(daily_counter.values())
    stat = sentiment_stats(daily_counter)

    line = "=" * 68
    out: list[str] = [
        line,
        f"  {date_str}  네이버 뉴스 일간 종합 인사이트",
        line,
        "",
        "[1] 분석 개요",
        f"    - 분석 신문사   : {len(press_counters)}개 ({', '.join(press_counters)})",
        f"    - 분석 카테고리 : {len(cat_counters)}개 ({', '.join(cat_counters)})",
        f"    - 분석 조합     : {len(records)}건 (신문사 x 카테고리)",
        f"    - 수집 기사     : {total_articles:,}건",
        f"    - 추출 키워드   : {len(daily_counter):,}종 (누적 빈도 {total_freq:,}회)",
        "",
        "[2] 오늘의 핵심 키워드 TOP 10",
    ]
    for rank, (word, freq) in enumerate(daily_counter.most_common(10), start=1):
        share = freq / total_freq * 100 if total_freq else 0
        out.append(f"    {rank:2d}. {word:<12s} {freq:5,}회  ({share:4.1f}%)")

    out += [
        "",
        "[3] 감성 분석 요약",
        f"    - 긍정 : {stat['pos_kinds']}종 / 총 {stat['pos_total']:,}회",
        f"    - 부정 : {stat['neg_kinds']}종 / 총 {stat['neg_total']:,}회",
        f"    - 감성지수 : {stat['index']:+.1f}  (범위 -100 ~ +100, 음수일수록 부정 우세)",
        f"    - 대표 긍정어 : {_top_phrase(stat['positive'], 5) or '없음'}",
        f"    - 대표 부정어 : {_top_phrase(stat['negative'], 5) or '없음'}",
        "",
    ]
    if stat["index"] <= -20:
        out.append("    => 사건·사고, 수사, 갈등 등 부정 어휘가 하루 보도를 주도했습니다.")
    elif stat["index"] < -5:
        out.append("    => 부정 어휘가 다소 우세하나 한쪽으로 크게 치우치지는 않았습니다.")
    elif stat["index"] <= 5:
        out.append("    => 긍정과 부정 어휘가 비슷한 비중으로 나타났습니다.")
    elif stat["index"] < 20:
        out.append("    => 성장·협력 등 긍정 어휘가 다소 우세한 하루였습니다.")
    else:
        out.append("    => 성과·개선 등 긍정 어휘가 하루 보도를 주도했습니다.")

    out += ["", "[4] 신문사별 요약"]
    for press in sorted(press_counters, key=lambda p: -sum(press_counters[p].values())):
        pstat = sentiment_stats(press_counters[press])
        out.append(f"    - {_unit_insight(press, press_counters[press], press_articles[press], pstat)}")

    out += ["", "[5] 카테고리별 요약"]
    for cat in sorted(cat_counters, key=lambda c: -sum(cat_counters[c].values())):
        cstat = sentiment_stats(cat_counters[cat])
        out.append(f"    - {_unit_insight(cat, cat_counters[cat], cat_articles[cat], cstat)}")

    # 공통 의제 / 단독 보도는 신문사가 2개 이상일 때만 의미가 있다.
    if len(press_counters) >= 2:
        common = [w for w in daily_counter
                   if all(w in press_counters[p] for p in press_counters)]
        common.sort(key=lambda w: -daily_counter[w])
        out += ["", f"[6] 전 신문사 공통 키워드 (오늘의 공통 의제) — {len(common)}종"]
        if common:
            for word in common[:15]:
                out.append(f"    - {word} ({daily_counter[word]}회)")
        else:
            out.append("    - 모든 신문사에 공통으로 등장한 키워드가 없습니다.")

        out += ["", "[7] 단독 키워드 (해당 신문사에서만 등장)"]
        for press in press_counters:
            others = set()
            for other in press_counters:
                if other != press:
                    others.update(press_counters[other])
            only = [w for w in press_counters[press] if w not in others]
            only.sort(key=lambda w: -press_counters[press][w])
            preview = ", ".join(f"{w}({press_counters[press][w]})" for w in only[:8])
            out.append(f"    - {press}: {len(only)}종" + (f" | {preview}" if preview else ""))

    out += [
        "",
        line,
        "  ※ 이 리포트는 명사 추출 + 불용어 제거를 마친 키워드 빈도와, 내장 감성",
        "     사전(POSITIVE_WORDS / NEGATIVE_WORDS) 기준의 규칙 기반 집계입니다.",
        "     문맥·반어·인용까지 판별하는 문장 단위 감성 분석은 아닙니다.",
        f"  ※ 생성 시각: {datetime.now():%Y-%m-%d %H:%M:%S}",
        line,
        "",
    ]
    return "\n".join(out)


def save_daily_insight_csv(daily_counter: Counter, records: list[dict],
                            out_path: Path, date_obj: datetime) -> None:
    """일 단위 인사이트를 종합 / 신문사별 / 카테고리별 행으로 나눠 CSV로 저장한다.

    한 행이 하나의 분석 단위이므로 엑셀 피벗이나 pandas 로 바로 집계할 수 있다.
    같은 날 다시 실행하면 덮어쓴다.
    """
    date_str = date_obj.strftime("%Y-%m-%d")

    press_counters: dict[str, Counter] = defaultdict(Counter)
    cat_counters: dict[str, Counter] = defaultdict(Counter)
    press_articles: dict[str, int] = defaultdict(int)
    cat_articles: dict[str, int] = defaultdict(int)
    for r in records:
        press_counters[r["press"]].update(r["counter"])
        cat_counters[r["category"]].update(r["counter"])
        press_articles[r["press"]] += r["articles"]
        cat_articles[r["category"]] += r["articles"]

    units: list[tuple[str, str, Counter, int]] = [
        ("종합", "전체", daily_counter, sum(press_articles.values())),
    ]
    units += [("신문사", p, press_counters[p], press_articles[p]) for p in press_counters]
    units += [("카테고리", c, cat_counters[c], cat_articles[c]) for c in cat_counters]
    units += [("신문사x카테고리", f"{r['press']}/{r['category']}", r["counter"], r["articles"])
               for r in records]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "날짜", "분석단위", "대상", "기사수", "키워드종수", "누적빈도",
            "긍정단어수", "긍정총빈도", "부정단어수", "부정총빈도", "감성지수",
            "상위키워드TOP5", "대표긍정어TOP3", "대표부정어TOP3", "인사이트",
        ])
        for unit, target, counter, articles in units:
            stat = sentiment_stats(counter)
            writer.writerow([
                date_str, unit, target, articles, len(counter), sum(counter.values()),
                stat["pos_kinds"], stat["pos_total"], stat["neg_kinds"], stat["neg_total"],
                stat["index"],
                _top_phrase(counter, 5),
                _top_phrase(stat["positive"], 3),
                _top_phrase(stat["negative"], 3),
                _unit_insight(target, counter, articles, stat),
            ])

    log.info("일간 인사이트 CSV 저장: %s (%d행)", out_path.name, len(units))


def load_saved_units(date_obj: datetime) -> list[dict]:
    """그날 이미 저장돼 있는 신문사/카테고리별 결과를 디스크에서 읽어 온다.

    일간 종합을 "이번 실행에 포함된 조합"만으로 만들면, 한 신문사만 다시 돌렸을 때
    그날의 종합 그래프와 인사이트가 그 신문사 것으로 덮어써진다. 그래서 이번 실행에
    없는 조합은 앞서 저장해 둔 `..._키워드빈도_*.csv` 에서 복원해 함께 합산한다.
    덕분에 전체를 다시 돌리지 않고 빠진 언론사만 채워 넣을 수 있다.

    기사 수는 같은 폴더의 `..._insight.csv` 에서 읽는다(조합당 한 행만 유지됨).
    """
    ymd = f"{date_obj:%Y%m%d}"
    day_dir = BASE_DIR / f"{date_obj:%Y}" / f"{date_obj:%m}" / f"{date_obj:%d}"
    units: list[dict] = []
    if not day_dir.exists():
        return units

    for press_dir in sorted(p for p in day_dir.iterdir() if p.is_dir()):
        for cat_dir in sorted(c for c in press_dir.iterdir() if c.is_dir()):
            press, category = press_dir.name, cat_dir.name
            kw_path = cat_dir / f"{press}_{category}_키워드빈도_{ymd}.csv"
            if not kw_path.exists():
                continue

            counter: Counter = Counter()
            try:
                with open(kw_path, encoding="utf-8-sig", newline="") as f:
                    for r in csv.DictReader(f):
                        try:
                            counter[r["단어"]] = int(r["빈도수"])
                        except (KeyError, TypeError, ValueError):
                            continue
            except OSError as e:
                log.warning("기존 결과 읽기 실패(%s): %s", kw_path.name, e)
                continue
            if not counter:
                continue

            articles = 0
            ins_path = cat_dir / f"{press}_{category}_insight.csv"
            if ins_path.exists():
                try:
                    with open(ins_path, encoding="utf-8-sig", newline="") as f:
                        for r in csv.DictReader(f):
                            try:
                                articles = int(r["기사수"])
                            except (KeyError, TypeError, ValueError):
                                pass
                except OSError:
                    pass

            units.append({"press": press, "category": category,
                           "counter": counter, "articles": articles})
    return units


def build_daily_summary(records: list[dict], date_obj: datetime) -> None:
    """그날의 전 신문사 x 전 카테고리 결과를 합산해 일 단위 산출물을 만든다.

    이번 실행 결과(records)와 디스크에 이미 있던 결과(load_saved_units)를 합쳐서
    쓰므로, 일부 조합만 다시 돌려도 일간 종합은 항상 그날 전체를 반영한다.
    같은 조합이 양쪽에 있으면 이번 실행 결과를 쓴다.

    저장 위치는 날짜 폴더 바로 아래(News/{YYYY}/{MM}/{DD}/)로,
    개별 신문사/카테고리 폴더보다 한 단계 위에 놓여 한눈에 보이게 한다.

    산출물: 그래프 4종 + 키워드빈도/감성기초자료 CSV 2종
            + 일간 인사이트 리포트(TXT) + 일간 인사이트 요약(CSV)
    """
    merged: dict[tuple[str, str], dict] = {
        (u["press"], u["category"]): u for u in load_saved_units(date_obj)
    }
    current_keys = {(r["press"], r["category"]) for r in records}
    merged.update({(r["press"], r["category"]): r for r in records})
    records = [merged[k] for k in sorted(merged)]

    daily_counter: Counter = Counter()
    for r in records:
        daily_counter.update(r["counter"])

    if not daily_counter:
        log.warning("일간 종합 산출물 생략: 집계된 키워드가 없습니다.")
        return

    log.info("일간 종합 집계 대상 %d조합 (이번 실행 %d + 기존 결과 재사용 %d)",
              len(records), len(current_keys), len(merged) - len(current_keys))

    date_str = date_obj.strftime("%Y-%m-%d")
    ymd = f"{date_obj:%Y%m%d}"
    day_dir = BASE_DIR / f"{date_obj:%Y}" / f"{date_obj:%m}" / f"{date_obj:%d}"

    save_graph_set(
        daily_counter, day_dir, "일간종합", ymd, date_str,
        scope=TITLE_SCOPE_DAILY, category=TITLE_CATEGORY_DAILY,
        top_n_chart=TOP_N_CHART_DAILY, max_words=TOP_N_NOUNS_DAILY,
    )

    # 일 단위 상세 인사이트 — 사람이 읽는 리포트(TXT)와 집계용 표(CSV) 두 가지.
    report = generate_daily_insight_report(daily_counter, records, date_obj)
    report_path = day_dir / f"일간종합_인사이트_{ymd}.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8-sig") as f:
        f.write(report)
    log.info("일간 인사이트 리포트 저장: %s", report_path.name)

    save_daily_insight_csv(daily_counter, records,
                            day_dir / f"일간종합_인사이트_{ymd}.csv", date_obj)

    stat = sentiment_stats(daily_counter)
    log.info("일간 종합 산출물 저장 완료: %s", day_dir)
    log.info("  - 집계 단어 %d종 / 긍정어 %d종 / 부정어 %d종 / 감성지수 %+.1f",
              len(daily_counter), stat["pos_kinds"], stat["neg_kinds"], stat["index"])


# ====================================================================
# 6. 인사이트 생성 / CSV 저장
# ====================================================================

def generate_insight(press: str, category: str, date_str: str,
                      articles: list[Article], counter: Counter) -> str:
    if not counter or not articles:
        return f"{date_str} {press} {category}: 수집된 기사가 없어 인사이트를 생성하지 못했습니다."

    top5 = counter.most_common(5)
    keyword_phrase = ", ".join(f"'{w}'({c}회)" for w, c in top5)
    sample_title = articles[0].title

    return (
        f"{date_str} {press}({category}) 기사 {len(articles)}건 분석 결과, "
        f"상위 키워드는 {keyword_phrase} 순으로 나타났습니다. "
        f"특히 '{top5[0][0]}' 관련 이슈가 가장 두드러졌으며, "
        f"대표 헤드라인은 \"{sample_title}\" 입니다."
    )


# 인사이트 CSV 의 행을 구분하는 키. 이 세 값이 같으면 같은 분석 단위로 본다.
INSIGHT_KEY_FIELDS = ("날짜", "언론사", "카테고리")


def upsert_csv_row(csv_path: Path, row: dict,
                    key_fields: tuple = INSIGHT_KEY_FIELDS) -> None:
    """같은 키의 기존 행이 있으면 교체하고, 없으면 새로 추가한다.

    그냥 append 하면 같은 날 같은 조합을 다시 돌릴 때마다 행이 중복 누적된다.
    (예: 한 언론사만 다시 분석 -> 그 조합의 행이 두 벌 쌓임)
    키가 같은 행을 새 값으로 갈아끼우므로, 몇 번을 다시 돌려도 조합당 한 행만 남는다.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(row.keys())
    existing: list[dict] = []
    if csv_path.exists():
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                fieldnames = reader.fieldnames
                existing = list(reader)

    key = tuple(str(row.get(k, "")) for k in key_fields)
    kept = [r for r in existing
             if tuple(str(r.get(k, "")) for k in key_fields) != key]
    kept.append({k: row.get(k, "") for k in fieldnames})

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)


# ====================================================================
# 7. 언론사 × 카테고리 단위 처리
# ====================================================================

def process_one(press: str, category: str, oid: str, date_obj: datetime, debug: bool,
                 fetch_full_text: bool = True) -> tuple[bool, Counter, int]:
    date_str = date_obj.strftime("%Y-%m-%d")
    out_dir = BASE_DIR / f"{date_obj:%Y}" / f"{date_obj:%m}" / f"{date_obj:%d}" / press / category
    started = time.time()

    try:
        articles = collect_articles(oid, press, category, debug=debug)
        time.sleep(REQUEST_DELAY_SEC)

        # 분석 대상 텍스트 = 기사 제목 전체 + (기본 설정 시) 본문 일부.
        # 본문은 기사 1건당 페이지 요청이 추가로 들기 때문에 MAX_ARTICLES_FOR_TEXT
        # 개까지만 가져오고, 나머지 기사는 제목만으로 분석에 포함시킨다.
        texts = [a.title for a in articles]
        if fetch_full_text:
            for article in articles[:MAX_ARTICLES_FOR_TEXT]:
                body_text = fetch_article_text(article.url)
                if body_text:
                    texts.append(body_text)
                time.sleep(ARTICLE_REQUEST_DELAY_SEC)

        counter = extract_noun_counter(texts, top_n=TOP_N_NOUNS)

        # 신문사 x 카테고리 단위 그래프 4종 (빈도 워드클라우드/바차트 + 감성 워드클라우드/바차트)
        save_graph_set(
            counter, out_dir, f"{press}_{category}", f"{date_obj:%Y%m%d}", date_str,
            scope=press, category=category,
        )

        insight_text = generate_insight(press, category, date_str, articles, counter)
        top5 = counter.most_common(5)
        row = {
            "날짜": date_str,
            "언론사": press,
            "카테고리": category,
            "기사수": len(articles),
            "상위키워드": "; ".join(f"{w}({c})" for w, c in top5),
            "인사이트": insight_text,
            "생성시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "상태": "성공" if articles else "기사없음",
        }

        upsert_csv_row(out_dir / f"{press}_{category}_insight.csv", row)
        upsert_csv_row(MASTER_CSV, row)

        elapsed = time.time() - started
        log.info("[%s/%s] 완료 (기사 %d건, %.1f초)", press, category, len(articles), elapsed)
        return True, counter, len(articles)

    except Exception as e:
        log.exception("[%s/%s] 처리 중 오류 발생: %s", press, category, e)
        row = {
            "날짜": date_str, "언론사": press, "카테고리": category,
            "기사수": 0, "상위키워드": "", "인사이트": f"오류: {e}",
            "생성시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "상태": "실패",
        }
        try:
            upsert_csv_row(MASTER_CSV, row)
        except Exception:
            pass
        return False, Counter(), 0


# ====================================================================
# 8. 메인
# ====================================================================

def parse_args():
    p = argparse.ArgumentParser(description="네이버 뉴스 언론사별 명사 빈도/워드클라우드/인사이트 자동 분석")
    p.add_argument("--date", type=str, default=None, help="분석 대상 날짜 YYYYMMDD (기본값: 오늘)")
    p.add_argument("--press", type=str, default=None, help="특정 언론사만 실행 (콤마로 구분, 예: 조선일보,문화일보)")
    p.add_argument("--category", type=str, default=None, help="특정 카테고리만 실행 (콤마로 구분, 예: 경제,사회)")
    p.add_argument("--debug", action="store_true", help="디버그 모드 (기사 0건 시 원본 HTML 저장 + 상세 로그)")
    p.add_argument("--no-fulltext", action="store_true",
                    help="기사 본문 수집을 건너뛰고 제목만으로 분석 (빠른 테스트용, 요청 수 절감)")
    return p.parse_args()


def main():
    args = parse_args()
    global log
    log = setup_logging(debug=args.debug)

    date_obj = datetime.strptime(args.date, "%Y%m%d") if args.date else datetime.now()
    press_targets = [p.strip() for p in args.press.split(",")] if args.press else PRESS_LIST
    category_targets = [c.strip() for c in args.category.split(",")] if args.category else list(CATEGORIES.keys())
    fetch_full_text = FETCH_FULL_TEXT_DEFAULT and not args.no_fulltext

    log.info("=" * 60)
    log.info("NAVER 뉴스 분석 시작: %s / 언론사 %d개 x 카테고리 %d개 / 본문 반영: %s",
              date_obj.strftime("%Y-%m-%d"), len(press_targets), len(category_targets),
              "예" if fetch_full_text else "아니오(제목만)")
    log.info("=" * 60)

    oid_map = get_press_oid_map()

    success, fail, skipped = 0, 0, 0
    # 하루치 전 언론사 x 전 카테고리 명사 빈도를 하나로 합산할 Counter.
    # 개별 조합의 Counter 를 그대로 더하므로 조합 수만큼 빈도가 누적된다.
    # 신문사/카테고리별 비교 인사이트를 만들기 위해 조합별 결과를 모아 둔다.
    records: list[dict] = []

    for press in press_targets:
        oid = resolve_oid(press, oid_map)
        if not oid:
            # 이름이 한 글자만 달라도 조회가 실패하므로, 비슷한 이름을 함께 보여준다.
            grams = {press[i:i + 2] for i in range(len(press) - 1)}
            similar = sorted(k for k in oid_map if any(g in k for g in grams))
            log.error("[%s] 언론사 고유번호(oid)를 찾지 못해 건너뜁니다. "
                      "PRESS_LIST 의 이름이 네이버 등재명과 다를 수 있습니다.", press)
            if similar:
                log.error("    비슷한 이름: %s",
                           ", ".join(f"{k}({oid_map[k]})" for k in similar[:8]))
            log.error("    이름을 고치거나 PRESS_OID_FALLBACK 에 직접 값을 넣어 주세요.")
            skipped += len(category_targets)
            continue

        for category in category_targets:
            if category not in CATEGORIES:
                log.warning("정의되지 않은 카테고리 '%s' - 건너뜁니다.", category)
                continue
            ok, counter, n_articles = process_one(
                press, category, oid, date_obj, debug=args.debug,
                fetch_full_text=fetch_full_text)
            success += int(ok)
            fail += int(not ok)
            if ok and counter:
                records.append({"press": press, "category": category,
                                 "counter": counter, "articles": n_articles})

    # 개별 조합 처리가 모두 끝난 뒤, 하루치를 취합한 일간 종합 산출물을 만든다.
    # 이번 실행에 없는 조합은 디스크에 저장된 기존 결과에서 채워 넣는다.
    build_daily_summary(records, date_obj)

    log.info("=" * 60)
    log.info("분석 종료: 성공 %d건 / 실패 %d건 / 건너뜀 %d건", success, fail, skipped)
    log.info("통합 인사이트 CSV: %s", MASTER_CSV)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
