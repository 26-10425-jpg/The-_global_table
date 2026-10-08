import json
import os
import random
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="THE GLOBAL TABLE",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================
# 설정
# =====================================================
TEACHER_PIN = "1234"  # 결과 확인 화면 비밀번호 (꼭 바꿔서 쓰세요)
RESULT_FILE = Path(__file__).with_name("global_table_results.json")

# =====================================================
# 기본 데이터
# =====================================================
# 국가 순서(= reaction 리스트 순서): 대한민국, 미국, 중국, 일본, 프랑스, 인도, 케냐
COUNTRIES = {
    "대한민국": {
        "flag": "🇰🇷",
        "interest": "경제 성장 · 안보 안정 · 국제협력",
        "desc": "경제적 안정과 국제협력을 함께 고려하는 교육용 설정입니다."
    },
    "미국": {
        "flag": "🇺🇸",
        "interest": "경제적 영향력 · 책임 분담 · 국가이익",
        "desc": "국제적 영향력과 국가 간 책임 분담을 고려하는 교육용 설정입니다."
    },
    "중국": {
        "flag": "🇨🇳",
        "interest": "경제 발전 · 주권 · 책임의 차이",
        "desc": "경제 발전과 국가 주권, 국가별 책임 차이를 고려하는 교육용 설정입니다."
    },
    "일본": {
        "flag": "🇯🇵",
        "interest": "경제 안정 · 국제협력 · 지역 안정",
        "desc": "경제적 안정과 국제협력을 고려하는 교육용 설정입니다."
    },
    "프랑스": {
        "flag": "🇫🇷",
        "interest": "다자주의 · 국제규범 · 공동 대응",
        "desc": "다자주의와 국제규범을 중요하게 고려하는 교육용 설정입니다."
    },
    "인도": {
        "flag": "🇮🇳",
        "interest": "경제 성장 · 개발 권리 · 개도국 대변",
        "desc": "개발 권리와 국제적 책임 사이의 균형을 고려하는 교육용 설정입니다."
    },
    "케냐": {
        "flag": "🇰🇪",
        "interest": "기후 취약성 · 지원 확대 · 수용국 부담",
        "desc": "국제적 지원과 책임 분담의 공정성을 중요하게 고려하는 교육용 설정입니다."
    },
}

# 진영(블록) 구도 - 교육용 단순화
BLOCS = {
    "선진국 연대": ["미국", "일본", "프랑스"],
    "개도국 연대": ["중국", "인도", "케냐"],
    "중견국(가교)": ["대한민국"],
}
BLOC_NOTES = {
    "선진국 연대": "재정·기술 지원을 제공하는 쪽에 가까운 국가들",
    "개도국 연대": "G77+중국처럼 개발 권리와 지원을 요구하는 쪽에 가까운 국가들",
    "중견국(가교)": "선진국과 개도국 사이에서 가교 역할을 하는 중견국",
}
OPPOSING = {"선진국 연대": "개도국 연대", "개도국 연대": "선진국 연대"}

AGENDAS = {
    "기후변화 대응": {
        "icon": "🌡️",
        "description": "국제기후기금과 국가별 책임을 어떻게 정할 것인가?"
    },
    "국제 난민 문제": {
        "icon": "🧑‍🤝‍🧑",
        "description": "난민 보호와 국제사회의 책임을 어떻게 분담할 것인가?"
    },
    "팬데믹·백신 분배": {
        "icon": "💉",
        "description": "백신과 의료 자원을 누가, 어떻게 나눌 것인가?"
    },
    "AI·디지털 규범": {
        "icon": "🤖",
        "description": "인공지능과 데이터를 어떤 국제 규범으로 다룰 것인가?"
    },
}

# 1라운드 질문
QUESTIONS = {
    "기후변화 대응": (
        "국제기후기금의 재원은 어떻게 마련해야 할까요?",
        "국가마다 경제적 능력과 역사적 책임에 대한 입장이 다릅니다."
    ),
    "국제 난민 문제": (
        "난민 보호의 책임은 어떻게 분담해야 할까요?",
        "국가마다 수용 능력과 국경 관리, 인도적 책임에 대한 입장이 다릅니다."
    ),
    "팬데믹·백신 분배": (
        "팬데믹 백신은 어떤 방식으로 분배해야 할까요?",
        "국가마다 제약 산업, 구매력, 보건 체계가 달라 우선순위가 다릅니다."
    ),
    "AI·디지털 규범": (
        "인공지능은 어떤 방식으로 규제해야 할까요?",
        "국가마다 기술 경쟁력, 안보, 인권, 산업 육성에 대한 입장이 다릅니다."
    ),
}

# 결의안 문구 마무리
RESOLUTION_TAIL = {
    "기후변화 대응": "기후변화 공동 대응을 추진한다.",
    "국제 난민 문제": "난민 보호와 책임 분담을 추진한다.",
    "팬데믹·백신 분배": "백신 접근성 확대와 보건 협력을 추진한다.",
    "AI·디지털 규범": "AI와 디지털 기술에 대한 국제 규범을 마련한다.",
}

POSITIONS = {
    "기후변화 대응": {
        "대한민국": "국제적 공동 대응에 찬성하지만 경제적 부담의 형평성을 고려해야 합니다.",
        "미국": "국제협력에는 찬성하지만 각 국가의 경제적 능력을 고려해야 합니다.",
        "중국": "선진국과 개발도상국의 역사적·경제적 책임 차이를 고려해야 합니다.",
        "일본": "국제적 협력과 기술 지원을 중요하게 생각합니다.",
        "프랑스": "다자주의와 국제적 공동 책임을 강조합니다.",
        "인도": "역사적 배출 책임이 큰 선진국의 재정·기술 지원을 요구하며, 개발 권리와 에너지 접근성을 중요하게 생각합니다.",
        "케냐": "기후 피해에 취약한 개도국으로서 적응 지원과 손실·피해에 대한 재원 마련을 강조합니다.",
    },
    "국제 난민 문제": {
        "대한민국": "인도적 지원과 국가의 수용 능력 사이의 균형을 중요하게 생각합니다.",
        "미국": "국제적 책임 분담과 국경 관리 사이의 균형을 고려합니다.",
        "중국": "국가 주권과 지역적 책임을 중요하게 생각합니다.",
        "일본": "재정 지원과 국제적 협력을 통한 해결을 선호합니다.",
        "프랑스": "국제적 인권 기준과 공동 책임을 강조합니다.",
        "인도": "국경 관리와 국가 주권을 중시하며, 자국 여건에 맞는 방식의 인도적 지원을 선호합니다.",
        "케냐": "많은 난민을 수용해 온 국가로서 수용국의 부담을 국제사회가 함께 나눠야 한다고 강조합니다.",
    },
    "팬데믹·백신 분배": {
        "대한민국": "백신 생산 역량을 갖춘 국가로서 공급망 협력과 공평한 접근을 함께 중요하게 생각합니다.",
        "미국": "혁신을 위한 지식재산권 보호와 자국민 보호를 중시하면서 국제 지원도 병행하려 합니다.",
        "중국": "백신을 공공재로 보며 개도국에 대한 공급과 지원을 강조합니다.",
        "일본": "의료 기술과 재정 지원을 통한 국제 공조를 선호합니다.",
        "프랑스": "국제 보건 협력과 WHO 중심의 다자 체제를 강조합니다.",
        "인도": "백신 생산 대국이자 개도국으로서 공평한 접근과 지식재산권 유연성을 요구합니다.",
        "케냐": "백신 확보가 어려운 저소득 지역으로서 공평한 접근과 현지 생산 역량 확충을 강조합니다.",
    },
    "AI·디지털 규범": {
        "대한민국": "AI 산업 경쟁력과 안전한 활용을 함께 추구하며 국제 논의에 적극 참여합니다.",
        "미국": "혁신과 기술 리더십을 중시하며 과도한 규제에는 신중합니다.",
        "중국": "각국의 디지털 주권을 존중하고 유엔 중심의 AI 협력을 강조합니다.",
        "일본": "혁신을 해치지 않는 범위에서 국제적 상호운용성을 갖춘 규범을 선호합니다.",
        "프랑스": "인권과 윤리를 중시하는 규범과 유럽식 규제 접근을 지지합니다.",
        "인도": "AI의 포용적 활용과 개도국의 기술 접근, 혁신 육성을 중요하게 생각합니다.",
        "케냐": "기술 격차를 우려하며 역량 강화와 데이터 권리 보호를 강조합니다.",
    },
}

# 국가별 목표
COUNTRY_GOALS = {
    "기후변화 대응": {
        "대한민국": "경제적 부담의 형평성을 지키면서 국제 공동 대응에 참여하기",
        "미국": "국가별 경제 능력을 고려한 책임 분담 이끌어내기",
        "중국": "선진국과 개도국의 책임 차이를 결의안에 반영하기",
        "일본": "국제 협력과 기술 지원 체계 마련하기",
        "프랑스": "다자주의에 기반한 공동 책임 원칙 확립하기",
        "인도": "개발 권리를 지키면서 선진국의 재정·기술 지원 확보하기",
        "케냐": "기후 취약국을 위한 적응·손실·피해 재원 확보하기",
    },
    "국제 난민 문제": {
        "대한민국": "인도적 지원과 수용 능력 사이의 균형 맞추기",
        "미국": "책임 분담을 이끌어내면서 국경 관리 권한 지키기",
        "중국": "국가 주권을 지키면서 지역적 책임 반영하기",
        "일본": "재정 지원과 국제 협력 중심의 해법 마련하기",
        "프랑스": "국제 인권 기준에 기반한 공동 책임 확립하기",
        "인도": "국가 주권과 자국 여건에 맞는 지원 방식 보장하기",
        "케냐": "수용국의 부담을 국제사회가 함께 나누게 하기",
    },
    "팬데믹·백신 분배": {
        "대한민국": "생산 역량을 활용하면서 공평한 백신 접근 체계에 기여하기",
        "미국": "지식재산권 보호와 국제 보건 지원의 균형 맞추기",
        "중국": "백신을 공공재로 보는 국제 공급 체계 마련하기",
        "일본": "기술·재정 지원 중심의 국제 공조 체계 마련하기",
        "프랑스": "WHO 중심의 다자 보건 협력 체계 강화하기",
        "인도": "공평한 접근과 지식재산권 유연성 확보하기",
        "케냐": "저소득국의 백신 접근성과 현지 생산 역량 확보하기",
    },
    "AI·디지털 규범": {
        "대한민국": "산업 경쟁력을 지키면서 신뢰할 수 있는 AI 규범에 참여하기",
        "미국": "혁신을 해치지 않는 유연한 규범 이끌어내기",
        "중국": "디지털 주권을 존중하는 유엔 중심 협력 틀 마련하기",
        "일본": "혁신과 상호운용성을 함께 보장하는 규범 마련하기",
        "프랑스": "인권과 투명성을 중시하는 공동 규범 확립하기",
        "인도": "포용적 AI 활용과 개도국의 기술 접근 확보하기",
        "케냐": "기술 격차 해소를 위한 역량 강화 지원 확보하기",
    },
}

# 국가별 투표 이유 (찬성 / 기권 / 반대)
VOTE_REASONS = {
    "기후변화 대응": {
        "대한민국": {
            "찬성": "공동 대응에 참여하면서도 부담의 형평성이 지켜졌다고 판단했습니다.",
            "기권": "방향에는 공감하지만 경제적 부담의 형평성이 충분히 보장되지 않아 입장을 유보했습니다.",
            "반대": "경제적 부담이 공정하게 배분되지 않는다고 판단했습니다.",
        },
        "미국": {
            "찬성": "국가별 경제 능력과 국익을 고려한 합의라고 판단했습니다.",
            "기권": "협력에는 공감하지만 자국의 부담 수준에 대해 확신하지 못했습니다.",
            "반대": "경제 능력이 충분히 고려되지 않거나 자국에 과도한 부담이 돌아온다고 판단했습니다.",
        },
        "중국": {
            "찬성": "선진국과 개도국의 책임 차이가 반영되었다고 판단했습니다.",
            "기권": "책임 차이가 일부만 반영되어 입장을 유보했습니다.",
            "반대": "역사적·경제적 책임 차이가 충분히 반영되지 않았다고 판단했습니다.",
        },
        "일본": {
            "찬성": "국제 협력과 기술 지원의 틀이 마련되었다고 판단했습니다.",
            "기권": "협력 방향에는 공감하지만 구체적인 이행 방식에 확신이 부족했습니다.",
            "반대": "실효성 있는 협력과 기술 지원 체계가 부족하다고 판단했습니다.",
        },
        "프랑스": {
            "찬성": "다자주의와 공동 책임의 원칙이 잘 반영되었다고 판단했습니다.",
            "기권": "공동 책임의 방향은 맞지만 국제 공조 장치가 충분하지 않다고 보았습니다.",
            "반대": "구속력 있는 공동 책임 체계가 부족하다고 판단했습니다.",
        },
        "인도": {
            "찬성": "선진국의 역사적 책임과 개발 권리가 반영되었다고 판단했습니다.",
            "기권": "일부 반영되었지만 재정·기술 지원 약속이 충분하지 않다고 보았습니다.",
            "반대": "개발 권리와 선진국의 역사적 책임이 충분히 반영되지 않았다고 판단했습니다.",
        },
        "케냐": {
            "찬성": "기후 취약국에 대한 적응 지원과 재원 마련이 반영되었다고 판단했습니다.",
            "기권": "지원 방향은 있으나 손실·피해 재원이 충분하지 않다고 보았습니다.",
            "반대": "기후 피해국에 대한 지원과 형평성이 부족하다고 판단했습니다.",
        },
    },
    "국제 난민 문제": {
        "대한민국": {
            "찬성": "인도적 지원과 국가의 수용 능력이 균형을 이루었다고 판단했습니다.",
            "기권": "인도적 책임에는 공감하지만 수용 능력에 대한 고려가 부족하다고 보았습니다.",
            "반대": "자국의 수용 능력을 넘어서는 부담이 생길 수 있다고 판단했습니다.",
        },
        "미국": {
            "찬성": "국제적 책임 분담과 국경 관리 권한이 함께 보장되었다고 판단했습니다.",
            "기권": "책임 분담에는 공감하지만 국경 관리 권한이 약해질 수 있다고 우려했습니다.",
            "반대": "책임 분담이 공정하지 않거나 국경 관리 권한이 침해된다고 판단했습니다.",
        },
        "중국": {
            "찬성": "국가 주권을 존중하면서 지역적 책임을 인정했다고 판단했습니다.",
            "기권": "주권 존중이 일부만 반영되어 입장을 유보했습니다.",
            "반대": "국가 주권이 충분히 존중되지 않는다고 판단했습니다.",
        },
        "일본": {
            "찬성": "재정 지원과 국제 협력 중심의 해법이 담겼다고 판단했습니다.",
            "기권": "협력 방향에는 공감하지만 구체적인 재정 분담 방식에 확신이 부족했습니다.",
            "반대": "현실적인 재정·협력 체계가 부족하다고 판단했습니다.",
        },
        "프랑스": {
            "찬성": "국제 인권 기준과 공동 책임이 충실히 반영되었다고 판단했습니다.",
            "기권": "공동 책임의 방향은 맞지만 인권 기준을 보장하는 장치가 부족하다고 보았습니다.",
            "반대": "국제 인권 기준과 공동 책임이 충분히 보장되지 않는다고 판단했습니다.",
        },
        "인도": {
            "찬성": "국가 주권과 자국 여건에 맞는 지원 방식이 존중되었다고 판단했습니다.",
            "기권": "인도적 지원에는 공감하지만 일률적인 부담에는 부담을 느꼈습니다.",
            "반대": "자국 여건과 국가 주권이 충분히 고려되지 않는다고 판단했습니다.",
        },
        "케냐": {
            "찬성": "난민 수용국의 부담을 국제사회가 함께 나누는 구조라고 판단했습니다.",
            "기권": "부담 분담의 방향은 있으나 수용국 지원이 충분하지 않다고 보았습니다.",
            "반대": "난민을 많이 수용해 온 국가의 부담이 충분히 분담되지 않는다고 판단했습니다.",
        },
    },
    "팬데믹·백신 분배": {
        "대한민국": {
            "찬성": "공평한 접근을 지원하면서 자국의 생산·공급망 역량도 활용할 수 있다고 판단했습니다.",
            "기권": "공평한 접근에는 공감하지만 생산·공급망 부담에 대해 확신이 부족했습니다.",
            "반대": "자국의 공급 안정과 산업 경쟁력에 부담이 크다고 판단했습니다.",
        },
        "미국": {
            "찬성": "혁신 유인과 국제 지원이 균형을 이루었다고 판단했습니다.",
            "기권": "국제 지원에는 공감하지만 지식재산권과 자국민 보호에 대한 우려가 남았습니다.",
            "반대": "지식재산권과 자국민 보호에 부정적인 영향을 준다고 판단했습니다.",
        },
        "중국": {
            "찬성": "백신을 공공재로 보고 개도국의 접근을 넓히는 방향이라고 판단했습니다.",
            "기권": "접근성 확대에는 공감하지만 구체적인 운영 방식에 대해 입장을 유보했습니다.",
            "반대": "개도국의 접근성과 공공재적 성격이 충분히 반영되지 않았다고 판단했습니다.",
        },
        "일본": {
            "찬성": "기술과 재정 지원을 통한 국제 공조 틀이 마련되었다고 판단했습니다.",
            "기권": "공조 방향에는 공감하지만 재정 분담과 기술 보호 방식에 확신이 부족했습니다.",
            "반대": "연구개발 유인을 해치거나 현실적인 공조 체계가 부족하다고 판단했습니다.",
        },
        "프랑스": {
            "찬성": "WHO 중심의 다자 보건 협력 원칙이 잘 반영되었다고 판단했습니다.",
            "기권": "공동 대응의 방향은 맞지만 다자 체제의 역할이 충분하지 않다고 보았습니다.",
            "반대": "국제 보건 협력과 다자 체제를 약화시킨다고 판단했습니다.",
        },
        "인도": {
            "찬성": "공평한 접근과 지식재산권 유연성이 반영되었다고 판단했습니다.",
            "기권": "접근성은 개선되지만 지식재산권과 생산 역량 문제가 충분히 다뤄지지 않았다고 보았습니다.",
            "반대": "개도국의 접근성과 지식재산권 유연성이 보장되지 않는다고 판단했습니다.",
        },
        "케냐": {
            "찬성": "저소득국의 백신 접근과 현지 생산 역량 확충이 반영되었다고 판단했습니다.",
            "기권": "접근성은 일부 개선되지만 공급 시기와 현지 생산 지원이 부족하다고 보았습니다.",
            "반대": "저소득국이 뒤로 밀리는 구조라고 판단했습니다.",
        },
    },
    "AI·디지털 규범": {
        "대한민국": {
            "찬성": "산업 경쟁력을 지키면서 신뢰할 수 있는 AI 규범이 마련되었다고 판단했습니다.",
            "기권": "규범의 필요성에는 공감하지만 산업에 미칠 영향이 불확실하다고 보았습니다.",
            "반대": "산업 경쟁력에 과도한 부담이 될 수 있다고 판단했습니다.",
        },
        "미국": {
            "찬성": "혁신을 해치지 않는 유연한 규범이라고 판단했습니다.",
            "기권": "협력에는 공감하지만 규제가 혁신과 기술 리더십을 약화시킬 수 있다고 우려했습니다.",
            "반대": "과도한 규제로 혁신과 기술 리더십을 해칠 수 있다고 판단했습니다.",
        },
        "중국": {
            "찬성": "각국의 디지털 주권이 존중되는 협력 틀이라고 판단했습니다.",
            "기권": "협력에는 공감하지만 디지털 주권의 보장 수준이 불충분하다고 보았습니다.",
            "반대": "디지털 주권을 제약하거나 특정 국가가 주도하는 규범이라고 판단했습니다.",
        },
        "일본": {
            "찬성": "혁신과 국제적 상호운용성이 함께 고려되었다고 판단했습니다.",
            "기권": "규범의 방향은 맞지만 국가 간 제도 조화 방식에 확신이 부족했습니다.",
            "반대": "혁신을 저해하거나 국가 간 규범이 서로 맞지 않을 수 있다고 판단했습니다.",
        },
        "프랑스": {
            "찬성": "인권과 투명성을 중시하는 공동 규범이 반영되었다고 판단했습니다.",
            "기권": "방향에는 공감하지만 인권 보호 장치가 충분히 구속력 있지 않다고 보았습니다.",
            "반대": "인권과 투명성 보호가 충분하지 않다고 판단했습니다.",
        },
        "인도": {
            "찬성": "포용적 AI 활용과 개도국의 기술 접근이 반영되었다고 판단했습니다.",
            "기권": "일부 반영되었지만 기술 접근과 혁신 여력에 대한 보장이 부족하다고 보았습니다.",
            "반대": "개도국의 혁신 여력과 기술 접근을 제약할 수 있다고 판단했습니다.",
        },
        "케냐": {
            "찬성": "기술 격차 해소와 역량 강화 지원이 반영되었다고 판단했습니다.",
            "기권": "규범은 마련되지만 역량 강화 지원이 충분하지 않다고 보았습니다.",
            "반대": "기술 강국 중심의 규범으로 격차가 더 커질 수 있다고 판단했습니다.",
        },
    },
}

# 1라운드 선택지
OPTIONS = {
    "기후변화 대응": [
        {
            "title": "모든 국가가 동일한 금액을 부담한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 0, "compromise": 1},
            "reaction": ["조건부 찬성", "긍정적", "우려", "긍정적", "긍정적", "반대", "반대"],
        },
        {
            "title": "경제 규모가 큰 국가가 더 많은 비용을 부담한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "조건부 찬성", "긍정적", "긍정적", "매우 긍정적", "조건부 찬성", "매우 긍정적"],
        },
        {
            "title": "선진국이 대부분의 비용을 부담한다.",
            "scores": {"cooperation": 1, "national": 1, "multi": 2, "compromise": 0},
            "reaction": ["긍정적", "반대", "매우 긍정적", "조건부 찬성", "긍정적", "매우 긍정적", "매우 긍정적"],
        },
        {
            "title": "각 국가가 자발적으로 기여한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "조건부 찬성", "긍정적", "우려", "조건부 찬성", "우려"],
        },
    ],
    "국제 난민 문제": [
        {
            "title": "모든 국가가 동일한 수의 난민을 수용한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 1, "compromise": 0},
            "reaction": ["조건부 찬성", "우려", "우려", "조건부 찬성", "긍정적", "우려", "반대"],
        },
        {
            "title": "경제적 능력이 높은 국가가 더 많은 책임을 부담한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "조건부 찬성", "긍정적", "긍정적", "매우 긍정적", "긍정적", "매우 긍정적"],
        },
        {
            "title": "국제기구가 난민 지원을 통합적으로 조정한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 2},
            "reaction": ["긍정적", "조건부 찬성", "조건부 찬성", "긍정적", "매우 긍정적", "조건부 찬성", "긍정적"],
        },
        {
            "title": "각 국가가 자국 상황에 따라 자율적으로 결정한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "긍정적", "조건부 찬성", "우려", "긍정적", "우려"],
        },
    ],
    "팬데믹·백신 분배": [
        {
            "title": "모든 국가에 인구 비례로 동일하게 배분한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["조건부 찬성", "반대", "긍정적", "우려", "긍정적", "긍정적", "매우 긍정적"],
        },
        {
            "title": "구매력이 높은 국가가 먼저 구매하고 나머지는 나중에 공급받는다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 0},
            "reaction": ["긍정적", "긍정적", "조건부 찬성", "긍정적", "우려", "반대", "반대"],
        },
        {
            "title": "선진국이 기금을 내서 공동 구매하고 저소득국에 우선 배분한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "우려", "긍정적", "조건부 찬성", "매우 긍정적", "긍정적", "매우 긍정적"],
        },
        {
            "title": "각국이 자국 생산·구매를 우선하고 여유분만 기증한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "긍정적", "긍정적", "반대", "조건부 찬성", "우려"],
        },
    ],
    "AI·디지털 규범": [
        {
            "title": "위험 수준에 따라 법적 구속력이 있는 국제 규제를 만든다.",
            "scores": {"cooperation": 2, "national": -1, "multi": 2, "compromise": 0},
            "reaction": ["조건부 찬성", "반대", "우려", "우려", "매우 긍정적", "우려", "긍정적"],
        },
        {
            "title": "기업과 국가의 자율 규범에 맡기고 혁신을 우선한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "조건부 찬성", "긍정적", "반대", "조건부 찬성", "반대"],
        },
        {
            "title": "법적 구속력은 없지만 국제 원칙과 가이드라인에 합의한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 1, "compromise": 2},
            "reaction": ["긍정적", "긍정적", "조건부 찬성", "긍정적", "조건부 찬성", "긍정적", "우려"],
        },
        {
            "title": "개도국의 기술 접근과 역량 강화를 지원하는 국제 기금을 만든다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["조건부 찬성", "우려", "긍정적", "조건부 찬성", "긍정적", "매우 긍정적", "매우 긍정적"],
        },
    ],
}

# 2라운드 선택지
SECOND_OPTIONS = {
    "기후변화 대응": [
        {
            "title": "모든 국가의 동일한 책임을 강조한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 0, "compromise": 1},
            "reaction": ["조건부 찬성", "긍정적", "우려", "긍정적", "긍정적", "반대", "반대"],
        },
        {
            "title": "국가의 경제적 능력에 따른 차등적 책임을 강조한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 2},
            "reaction": ["긍정적", "조건부 찬성", "긍정적", "긍정적", "매우 긍정적", "매우 긍정적", "매우 긍정적"],
        },
        {
            "title": "국제기구를 통한 공동 대응을 최우선으로 한다.",
            "scores": {"cooperation": 2, "national": -1, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "우려", "조건부 찬성", "긍정적", "매우 긍정적", "조건부 찬성", "긍정적"],
        },
        {
            "title": "각 국가의 자율적인 참여를 보장한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "긍정적", "조건부 찬성", "우려", "긍정적", "우려"],
        },
    ],
    "국제 난민 문제": [
        {
            "title": "모든 국가가 동일한 수의 난민을 수용한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 1, "compromise": 0},
            "reaction": ["조건부 찬성", "우려", "우려", "조건부 찬성", "긍정적", "우려", "반대"],
        },
        {
            "title": "경제적 능력이 높은 국가가 더 많은 책임을 부담한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "조건부 찬성", "긍정적", "긍정적", "매우 긍정적", "긍정적", "매우 긍정적"],
        },
        {
            "title": "국제기구가 난민 지원을 통합적으로 조정한다.",
            "scores": {"cooperation": 2, "national": -1, "multi": 2, "compromise": 2},
            "reaction": ["긍정적", "조건부 찬성", "우려", "긍정적", "매우 긍정적", "조건부 찬성", "긍정적"],
        },
        {
            "title": "각 국가가 자국 상황에 따라 자율적으로 결정한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "긍정적", "조건부 찬성", "우려", "긍정적", "우려"],
        },
    ],
    "팬데믹·백신 분배": [
        {
            "title": "의료 필수 물품에 대한 지식재산권을 일시 면제한다.",
            "scores": {"cooperation": 1, "national": 0, "multi": 1, "compromise": 0},
            "reaction": ["조건부 찬성", "반대", "긍정적", "우려", "조건부 찬성", "매우 긍정적", "매우 긍정적"],
        },
        {
            "title": "특허는 유지하되 기술 이전과 현지 생산 지원을 늘린다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 1, "compromise": 2},
            "reaction": ["긍정적", "조건부 찬성", "조건부 찬성", "긍정적", "긍정적", "긍정적", "긍정적"],
        },
        {
            "title": "WHO가 분배와 정보 공유를 총괄하는 국제 보건 체계를 강화한다.",
            "scores": {"cooperation": 2, "national": -1, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "반대", "조건부 찬성", "조건부 찬성", "매우 긍정적", "조건부 찬성", "긍정적"],
        },
        {
            "title": "국가의 보건 주권을 존중하고 자율적 협력에 맡긴다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["긍정적", "매우 긍정적", "긍정적", "조건부 찬성", "우려", "긍정적", "반대"],
        },
    ],
    "AI·디지털 규범": [
        {
            "title": "각국의 디지털 주권과 데이터 관리 권한을 존중한다.",
            "scores": {"cooperation": 0, "national": 2, "multi": -1, "compromise": 1},
            "reaction": ["조건부 찬성", "반대", "매우 긍정적", "우려", "우려", "긍정적", "긍정적"],
        },
        {
            "title": "인권 보호와 투명성을 모든 AI 개발의 공통 원칙으로 한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "조건부 찬성", "반대", "긍정적", "매우 긍정적", "조건부 찬성", "긍정적"],
        },
        {
            "title": "국제기구가 AI 안전 기준을 마련하고 점검한다.",
            "scores": {"cooperation": 2, "national": -1, "multi": 2, "compromise": 1},
            "reaction": ["긍정적", "반대", "우려", "조건부 찬성", "매우 긍정적", "조건부 찬성", "긍정적"],
        },
        {
            "title": "기술 격차 해소를 위한 지식 공유와 교육을 최우선으로 한다.",
            "scores": {"cooperation": 2, "national": 0, "multi": 1, "compromise": 2},
            "reaction": ["긍정적", "우려", "긍정적", "긍정적", "긍정적", "매우 긍정적", "매우 긍정적"],
        },
    ],
}

# 3라운드: 양자 협상 카드
DEALS = [
    {
        "label": "큰 양보 — 상대국의 핵심 요구를 폭넓게 수용한다",
        "desc": "상대국의 지지는 크게 높아지지만, 상대국과 반대 진영의 국가들은 불만을 가질 수 있고 우리나라의 목표 달성도도 일부 줄어듭니다.",
        "partner_bonus": 2, "opp_penalty": -1, "my_cost": -1,
        "scores": {"cooperation": 1, "national": -1, "multi": 0, "compromise": 2},
    },
    {
        "label": "조건부 양보 — 일부만 수용하고 대신 지지를 요구한다",
        "desc": "상대국의 지지가 조금 높아지고, 다른 국가의 불만이나 우리나라의 손실은 없습니다.",
        "partner_bonus": 1, "opp_penalty": 0, "my_cost": 0,
        "scores": {"cooperation": 0, "national": 0, "multi": 0, "compromise": 1},
    },
    {
        "label": "양자 협상 없이 기존 입장을 유지한다",
        "desc": "아무도 달라지지 않습니다. 대신 국익을 지켰다는 평가를 받습니다.",
        "partner_bonus": 0, "opp_penalty": 0, "my_cost": 0,
        "scores": {"cooperation": 0, "national": 1, "multi": 0, "compromise": 0},
    },
]

# 용어 해설 / 실제 사례 / 생각해 볼 질문
GLOSSARY = {
    "기후변화 대응": [
        ("CBDR-RC (공통의 그러나 차별화된 책임)",
         "기후변화는 모든 국가가 함께 대응해야 하지만, 역사적 배출 책임과 경제적 능력이 다르므로 책임의 크기도 달라야 한다는 원칙입니다. 1992년 기후변화협약에 담겼습니다."),
        ("손실과 피해 (Loss and Damage)",
         "감축과 적응만으로 막기 어려운 기후 피해에 대해 취약국을 지원하는 문제입니다. 누가, 얼마를 부담할지가 협상의 핵심 쟁점입니다."),
    ],
    "국제 난민 문제": [
        ("강제송환 금지 원칙 (non-refoulement)",
         "난민을 박해받을 위험이 있는 곳으로 되돌려 보내서는 안 된다는 원칙입니다. 1951년 난민협약 제33조에 규정되어 있고, 국제관습법으로도 널리 인정됩니다."),
        ("책임 분담 (burden-sharing)",
         "난민을 많이 수용하는 국가의 부담을 재정 지원, 제3국 재정착, 기술 지원 등으로 국제사회가 함께 나누는 개념입니다."),
    ],
    "팬데믹·백신 분배": [
        ("백신 민족주의",
         "자국민 접종을 위해 백신을 먼저 대량 확보해, 다른 나라의 접근이 늦어지는 현상을 말합니다. 코로나19 때 크게 논란이 되었습니다."),
        ("TRIPS 협정과 지식재산권 면제",
         "WTO의 지식재산권 협정(TRIPS)은 특허 보호의 기준을 정합니다. 위기 때 일부 보호를 면제하거나 완화해 생산을 늘리자는 주장과, 연구개발 유인을 해친다는 반론이 맞섭니다."),
    ],
    "AI·디지털 규범": [
        ("위험 기반 접근 (risk-based approach)",
         "AI를 위험 수준에 따라 나누어 규제 강도를 달리하는 방식입니다. 유럽연합의 AI법이 대표적인 예입니다."),
        ("디지털 주권",
         "각국이 자국 영토 안의 데이터와 디지털 인프라를 스스로 관리·통제할 권한이 있다는 관점입니다. 데이터 현지화 요구와 연결되며, 인터넷의 분절 문제와 맞닿아 있습니다."),
    ],
}

CASES = {
    "기후변화 대응": [
        ("파리협정 (2015)",
         "각국이 스스로 감축 목표(NDC)를 정해 제출하는 방식으로, 선진국과 개도국이 모두 참여하도록 만든 틀입니다. 시뮬레이션의 '자율적 참여'와 비슷하지만, 목표를 주기적으로 높이도록 하는 장치가 붙어 있습니다."),
        ("교토의정서 (1997)",
         "선진국에만 감축 의무를 부과해 '차등적 책임' 원칙을 적용한 사례입니다. 이후 주요 배출국의 참여 문제가 논쟁이 되었습니다."),
        ("녹색기후기금과 손실·피해 기금",
         "선진국이 개도국의 감축과 적응을 돕기 위해 재원을 모으는 기구가 있고, 2022년 COP27에서는 손실과 피해 기금 설립이 합의되었습니다."),
    ],
    "국제 난민 문제": [
        ("1951년 난민협약",
         "난민의 정의와 권리, 강제송환 금지 원칙을 규정한 국제 규범으로, 1967년 의정서로 적용 범위가 넓어졌습니다."),
        ("레바논·튀르키예의 난민 수용",
         "시리아 내전 이후 두 나라는 수백만 명 규모의 난민을 받아들였고, 레바논은 인구 대비 세계 최고 수준의 수용국으로 알려져 있습니다. 소득 수준이 높지 않은 나라가 큰 부담을 지는 구조가 책임 분담 논의의 핵심입니다."),
        ("케냐의 난민촌과 글로벌 컴팩트 (2018)",
         "케냐는 다답·카쿠마 난민촌 등에서 오랫동안 이웃 나라 난민을 수용해 왔습니다. 2018년 '난민에 관한 글로벌 컴팩트'는 수용국의 부담을 국제사회가 나누자는 방향을 제시했습니다."),
    ],
    "팬데믹·백신 분배": [
        ("COVAX (2020)",
         "WHO·Gavi 등이 주도해 백신을 공평하게 공급하려 한 국제 공동 구매 이니셔티브입니다. 고소득국의 선구매로 초기 공급이 지연되었다는 비판도 받았습니다."),
        ("WTO의 TRIPS 면제 논쟁",
         "2020년 인도와 남아프리카공화국이 코로나19 관련 지식재산권의 일시 면제를 제안했고, 2022년 WTO 각료회의에서 백신에 한정된 제한적 합의가 이루어졌습니다."),
        ("WHO 팬데믹 협약",
         "다음 팬데믹에 대비한 국제 협약으로, 2025년 WHO 총회에서 채택된 것으로 알려져 있습니다. 세부 이행 절차는 이후 협상 사안이므로 최신 진행 상황은 따로 확인해 보세요."),
    ],
    "AI·디지털 규범": [
        ("유럽연합 AI법",
         "AI를 위험 수준에 따라 나누어 규제하는 법으로, 2024년 발효되어 단계적으로 적용됩니다. '위험 기반 접근'의 대표 사례입니다."),
        ("AI 안전 정상회의 (2023 영국, 2024 서울)",
         "AI의 안전 문제를 다루는 국제 정상급 논의로, 2024년 서울 회의는 한국과 영국이 공동 개최했습니다. 구속력 없는 원칙과 협력 약속이 중심이었습니다."),
        ("유엔의 AI 거버넌스 논의",
         "2024년 유엔 총회는 안전하고 신뢰할 수 있는 AI에 관한 결의를 채택했고, 같은 해 채택된 글로벌 디지털 컴팩트에도 AI 거버넌스 내용이 담겼습니다."),
    ],
}

# 2라운드 선택별 맞춤 질문
THINK_BY_CHOICE = {
    "기후변화 대응": [
        "역사적 배출량이 전혀 다른 국가들에게 '동일한 책임'을 요구하는 것이 과연 공정할까요?",
        "'경제적 능력'만으로 책임을 나누면 역사적 배출 책임은 어떻게 반영할 수 있을까요? 지금은 큰 배출국이 된 신흥국의 책임은 어떻게 볼까요?",
        "국제기구가 각국의 정책을 점검하고 조정할 때, 국가 주권과 실효성 중 무엇을 더 우선해야 할까요?",
        "자율 참여는 참여국을 늘리지만 이행을 보장하기 어렵습니다. 다른 나라만 노력하고 나는 무임승차하는 문제를 어떻게 막을 수 있을까요?",
    ],
    "국제 난민 문제": [
        "국가마다 면적, 경제력, 이미 수용한 규모가 다른데 '같은 수'를 받는 것이 정말 공평할까요?",
        "돈으로 책임을 나누는 것(재정 지원)과 직접 난민을 수용하는 것은 같은 무게의 책임일까요?",
        "국제기구가 통합 조정하면 효율적일 수 있지만, 개별 국가의 결정권은 어떻게 보장할 수 있을까요?",
        "자율 결정은 주권을 존중하지만 보호 수준이 국가마다 크게 달라질 수 있습니다. 강제송환 금지 원칙은 어떻게 지킬 수 있을까요?",
    ],
    "팬데믹·백신 분배": [
        "특허를 일시 면제하면 접근성은 높아지지만 신약 개발의 유인은 줄어들 수 있습니다. 어떤 균형이 가능할까요?",
        "기술 이전의 비용은 누가 부담해야 할까요? 기업의 자발성에만 맡겨도 충분할까요?",
        "WHO에 강한 권한을 주는 것과 국가의 보건 주권 사이에서 어디에 선을 그어야 할까요?",
        "팬데믹처럼 국경을 넘는 위기에서 자율 협력만으로 충분할까요? 한 나라의 미접종이 모두의 위험이 된다면요?",
    ],
    "AI·디지털 규범": [
        "각국이 자국 방식으로 데이터를 통제하면 AI와 인터넷 생태계가 분절될 수 있습니다. 주권과 연결성 중 무엇이 우선일까요?",
        "인권 보호에는 모두가 공감하지만 구체적인 기준은 국가마다 다릅니다. 누가 그 기준을 정해야 할까요?",
        "국제기구가 AI 안전 기준을 점검하려면 기술 강국의 참여가 필요합니다. 어떻게 이들을 참여시킬 수 있을까요?",
        "기술 격차를 줄이기 위한 지식 공유와 교육은 기술 강국에게도 이익이 될까요?",
    ],
}

# 돌발 상황: 2라운드 직전에 무작위로 발생.
# 선택한 2라운드 원칙이 '공동 대응형'이면 coop, 아니면 solo 표의 점수가 각국의 표결 점수에 더해짐
EVENTS = {
    "기후변화 대응": [
        {
            "title": "초대형 태풍과 홍수 피해 속보",
            "desc": "회의 도중 취약 지역에서 대규모 홍수 피해가 전해졌습니다. 기후 피해에 대한 국제사회의 대응이 시험대에 올랐습니다.",
            "hint": "공동 대응을 강조하는 원칙을 택하면 피해에 민감한 국가들이 호응하고, 개별·자율 중심으로 가면 반발할 수 있습니다.",
            "coop": {"케냐": 1, "인도": 1, "프랑스": 1},
            "solo": {"케냐": -1, "인도": -1, "프랑스": -1},
        },
        {
            "title": "국제 에너지 가격 급등",
            "desc": "국제 에너지 가격이 급등해 각국의 경제 부담에 대한 우려가 커졌습니다.",
            "hint": "에너지 수입 의존도가 높은 국가들은 공동 부담이 큰 원칙에 신중해지고, 유연한 원칙에는 더 호의적입니다.",
            "coop": {"대한민국": -1, "일본": -1, "인도": -1},
            "solo": {"대한민국": 1, "미국": 1, "인도": 1},
        },
    ],
    "국제 난민 문제": [
        {
            "title": "인접 지역 분쟁으로 난민 급증",
            "desc": "인접 지역에서 새로운 분쟁이 터져 많은 난민이 국경으로 몰리고 있다는 속보가 들어왔습니다.",
            "hint": "공동 대응 원칙은 수용국과 인권을 중시하는 국가에 힘을 주고, 각자 알아서 하자는 쪽은 이들의 반발을 부릅니다.",
            "coop": {"케냐": 1, "프랑스": 1, "일본": 1},
            "solo": {"케냐": -1, "프랑스": -1},
        },
        {
            "title": "국내 반이민 여론 확산",
            "desc": "여러 나라에서 난민 수용에 대한 국내 반대 여론이 커지고 있습니다.",
            "hint": "국내 여론에 민감한 국가들은 공동 부담 원칙에 부담을 느끼고, 자율 결정을 선호하게 됩니다.",
            "coop": {"미국": -1, "프랑스": -1, "대한민국": -1},
            "solo": {"미국": 1, "중국": 1, "인도": 1},
        },
    ],
    "팬데믹·백신 분배": [
        {
            "title": "신종 감염병 확산 속보",
            "desc": "새로운 감염병이 여러 지역으로 빠르게 퍼지고 있다는 속보가 전해졌습니다. 국경을 넘는 위기에 대한 대응이 시급해졌습니다.",
            "hint": "공동 대응 원칙은 다자 협력을 중시하는 국가에 힘을 주고, 각자도생식 원칙은 취약 지역 국가의 반발을 부릅니다.",
            "coop": {"프랑스": 1, "케냐": 1, "일본": 1, "대한민국": 1},
            "solo": {"케냐": -1, "인도": -1, "프랑스": -1},
        },
        {
            "title": "제약사 백신 공급 지연",
            "desc": "주요 제약사의 백신 공급이 지연된다는 소식이 들어왔습니다. 한정된 물량을 누가 먼저 받을지가 더 민감해졌습니다.",
            "hint": "자국 확보가 급한 국가는 개별 대응을 선호하고, 공급이 늦어지는 국가는 공동 대응에 더 기댑니다.",
            "coop": {"케냐": 1, "인도": 1, "미국": -1},
            "solo": {"케냐": -1, "인도": -1, "미국": 1},
        },
    ],
    "AI·디지털 규범": [
        {
            "title": "딥페이크 선거 개입 사건",
            "desc": "AI로 만든 가짜 영상이 선거에 영향을 주었다는 사건이 알려져 AI 규제 요구가 커졌습니다.",
            "hint": "공동 규범과 안전 기준을 택하면 인권과 신뢰를 중시하는 국가들이 호응하고, 자율에 맡기면 이들의 우려가 커집니다.",
            "coop": {"프랑스": 1, "대한민국": 1, "일본": 1},
            "solo": {"프랑스": -1, "대한민국": -1},
        },
        {
            "title": "대규모 개인정보 유출 사고",
            "desc": "대형 AI 서비스에서 개인정보가 대규모로 유출되었다는 소식이 전해졌습니다.",
            "hint": "공동 대응 원칙은 데이터 권리 보호를 요구하는 국가에 힘을 주지만, 자국 기업과 주권을 우려하는 국가는 신중해집니다.",
            "coop": {"프랑스": 1, "케냐": 1, "중국": 1, "미국": -1},
            "solo": {"프랑스": -1, "케냐": -1},
        },
    ],
}

# 반응 → 점수
REACTION_SCORE = {"매우 긍정적": 2, "긍정적": 1, "조건부 찬성": 0, "우려": -1, "반대": -2}

RESULT_INFO = {
    "다자협력형": (
        "🤝",
        "국제기구와 국가 간 협력을 중요하게 생각하는 외교 전략입니다.",
        "국제제도와 상호의존성을 강조하는 자유주의적 국제정치 관점과 연결해 생각할 수 있습니다."
    ),
    "국익우선형": (
        "🛡️",
        "국가의 이익과 안정성을 우선적으로 고려하는 외교 전략입니다.",
        "국가의 생존과 힘, 국익의 중요성을 강조하는 현실주의적 관점과 연결해 생각할 수 있습니다."
    ),
    "균형외교형": (
        "⚖️",
        "국가의 이익과 국제협력 사이에서 타협점을 찾는 외교 전략입니다.",
        "실제 외교에서 나타나는 이해관계 조정과 협상 전략을 생각해 볼 수 있습니다."
    ),
    "국제주의형": (
        "🌐",
        "국제규범과 공동의 책임을 강조하는 외교 전략입니다.",
        "국제규범과 다자주의가 국가의 행동에 영향을 미칠 수 있다는 관점과 연결할 수 있습니다."
    ),
}

# =====================================================
# 상태 / 공통 함수
# =====================================================
DEFAULT_STATE = {
    "step": 0,
    "country": None,
    "agenda": None,
    "round1": None,
    "round2": None,
    "round3": None,
    "event": None,
    "logged": False,
    "scores": {"cooperation": 0, "national": 0, "multi": 0, "compromise": 0},
}

WIDGET_KEYS = ["r3_deal", "r3_partner"]


def new_game(country=None, agenda=None, step=0):
    game = DEFAULT_STATE.copy()
    game["scores"] = DEFAULT_STATE["scores"].copy()
    game["country"] = country
    game["agenda"] = agenda
    game["step"] = step
    st.session_state.game = game
    for key in WIDGET_KEYS:
        st.session_state.pop(key, None)


if "game" not in st.session_state:
    new_game()


def reset_game():
    new_game()
    st.rerun()


def restart_with(country):
    """같은 의제로 다른 국가를 대표해서 다시 시작"""
    agenda = st.session_state.game["agenda"]
    new_game(country=country, agenda=agenda, step=3)
    st.rerun()


def add_scores(values):
    for key, value in values.items():
        st.session_state.game["scores"][key] += value


def score_percent(value):
    # 대략 -2~5 범위를 0~100으로 변환
    return max(0, min(100, int(50 + value * 12.5)))


def bloc_of(country):
    for name, members in BLOCS.items():
        if country in members:
            return name
    return ""


def get_country_reactions(country):
    """선택한 두 라운드에 대한 해당 국가의 반응과 점수 합계(-4~4)"""
    g = st.session_state.game
    agenda = g["agenda"]
    idx = list(COUNTRIES.keys()).index(country)
    r1 = OPTIONS[agenda][g["round1"]]["reaction"][idx]
    r2 = SECOND_OPTIONS[agenda][g["round2"]]["reaction"][idx]
    return r1, r2, REACTION_SCORE[r1] + REACTION_SCORE[r2]


def get_deltas():
    """양자 협상이 각 국가의 표결 점수에 미치는 영향"""
    g = st.session_state.game
    deltas = {c: 0 for c in COUNTRIES}
    r3 = g.get("round3")
    if not r3 or r3["deal"] == 2:
        return deltas
    deal = DEALS[r3["deal"]]
    partner = r3["partner"]
    me = g["country"]
    deltas[partner] += deal["partner_bonus"]
    deltas[me] += deal["my_cost"]
    opp = OPPOSING.get(bloc_of(partner))
    if opp and deal["opp_penalty"]:
        for c in BLOCS[opp]:
            if c not in (partner, me):
                deltas[c] += deal["opp_penalty"]
    return deltas


def is_collective(option):
    """2라운드 원칙이 공동 대응형인지(협력·다자주의 점수가 높은지)"""
    return option["scores"]["cooperation"] >= 2 or option["scores"]["multi"] >= 2


def get_event():
    g = st.session_state.game
    idx = g.get("event")
    if idx is None or g.get("agenda") is None:
        return None
    return EVENTS[g["agenda"]][idx]


def get_event_deltas():
    """돌발 상황이 각 국가의 표결 점수에 미치는 영향"""
    g = st.session_state.game
    deltas = {c: 0 for c in COUNTRIES}
    ev = get_event()
    if not ev or g.get("round2") is None:
        return deltas
    option = SECOND_OPTIONS[g["agenda"]][g["round2"]]
    table = ev["coop"] if is_collective(option) else ev["solo"]
    for c, d in table.items():
        deltas[c] += d
    return deltas


def goal_percent_of(raw):
    return int((max(-4, min(4, raw)) + 4) / 8 * 100)


def mood_of(score):
    if score >= 1:
        return "우호적"
    if score == 0:
        return "유보적"
    return "비우호적"


def get_result():
    s = st.session_state.game["scores"]
    if abs(s["cooperation"] - s["multi"]) <= 1 and s["national"] <= 1:
        return "국제주의형"
    if s["national"] >= 3 and s["national"] > s["cooperation"] + 1:
        return "국익우선형"
    if s["cooperation"] >= 3 and s["multi"] >= 2:
        return "다자협력형"
    return "균형외교형"


def vote_icon(vote):
    return "🟢" if vote == "찬성" else "🟡" if vote == "기권" else "🔴"


def render_event():
    ev = get_event()
    if not ev:
        return
    affected = sorted(set(ev["coop"]) | set(ev["solo"]), key=list(COUNTRIES).index)
    flags = " ".join(f"{COUNTRIES[c]['flag']} {c}" for c in affected)
    st.markdown(f"""
    <div class="event-card">
        <span class="badge" style="background:#ffe3e0; color:#a12a1f;">⚡ 돌발 상황 · 속보</span>
        <h3>{ev['title']}</h3>
        <p>{ev['desc']}</p>
        <p class="small-note" style="margin-top:8px;">💡 {ev['hint']}</p>
        <p class="small-note" style="margin:4px 0 0;">입장이 흔들릴 수 있는 국가: {flags}</p>
    </div>
    """, unsafe_allow_html=True)


def render_event_effect():
    ev = get_event()
    g = st.session_state.game
    if not ev or g.get("round2") is None:
        return
    option = SECOND_OPTIONS[g["agenda"]][g["round2"]]
    collective = is_collective(option)
    table = ev["coop"] if collective else ev["solo"]
    label = "공동 대응형 원칙" if collective else "개별·자율 중심 원칙"
    parts = " · ".join(f"{COUNTRIES[c]['flag']} {c} {d:+d}" for c, d in table.items())
    st.warning(f"⚡ 돌발 상황의 영향 — 당신이 고른 {label}에 대해: {parts}")


def render_blocs(my_country=None):
    st.markdown("**🧭 국제회의의 진영 구도**")
    cols = st.columns(len(BLOCS))
    for col, (name, members) in zip(cols, BLOCS.items()):
        with col:
            flags = " ".join(
                f"{COUNTRIES[m]['flag']} {m}{' ⭐' if m == my_country else ''}" for m in members
            )
            st.markdown(
                f"<div class='card' style='padding:16px 18px;'>"
                f"<span class='badge'>{name}</span>"
                f"<p style='margin:10px 0 4px; font-weight:700;'>{flags}</p>"
                f"<p class='small-note' style='margin:0;'>{BLOC_NOTES[name]}</p></div>",
                unsafe_allow_html=True,
            )
    st.caption("※ 진영 구분은 이해를 돕기 위한 교육용 단순화이며, 실제 국가들의 입장은 의제마다 다를 수 있습니다.")


# ---------- 수업용 기록 ----------
def load_results():
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_result(record):
    data = load_results()
    data.append(record)
    fd, tmp_path = tempfile.mkstemp(dir=str(RESULT_FILE.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp_path, RESULT_FILE)


def clear_results():
    try:
        os.remove(RESULT_FILE)
    except FileNotFoundError:
        pass


# =====================================================
# 스타일
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: #f5f8fc;
}

.block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, rgba(7,21,43,.98), rgba(16,55,96,.96));
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 28px;
    padding: 42px 42px 38px;
    color: white;
    text-align: center;
    box-shadow: 0 20px 60px rgba(3,12,30,.25);
    margin-bottom: 28px;
    overflow: visible;
}

.hero h1 {
    font-size: clamp(2.5rem, 5.5vw, 4rem);
    line-height: 1.12;
    letter-spacing: 3px;
    margin: 6px 0 14px;
    font-weight: 800;
    white-space: nowrap;
}

.hero p {
    color: #dce8f7;
    font-size: 1.1rem;
}

.section-title {
    font-size: 2rem;
    font-weight: 800;
    color: #10233f;
    margin: 1rem 0 .35rem;
}

.subtitle {
    color: #607089;
    margin-bottom: 1.5rem;
}

.card {
    background: rgba(255,255,255,.96);
    border: 1px solid #dbe4ef;
    border-radius: 20px;
    padding: 24px;
    margin: 10px 0;
    box-shadow: 0 8px 24px rgba(24,48,80,.08);
}

.country-card {
    height: 270px;
    min-height: 270px;
    box-sizing: border-box;
    overflow: hidden;
    padding-bottom: 22px;
}

.country-card h3 {
    font-size: 1.35rem;
    line-height: 1.2;
    margin: 8px 0 12px;
    white-space: nowrap;
}

.country-card p {
    line-height: 1.5;
    margin-top: 8px;
    margin-bottom: 0;
}

.feature-card {
    min-height: 190px;
    height: 190px;
    box-sizing: border-box;
}

.badge {
    display: inline-block;
    background: #e8f1fb;
    color: #174d82;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: .8rem;
    font-weight: 700;
}

.goal-card {
    background: #eef6ff;
    border: 1px solid #b9d4f0;
    border-radius: 20px;
    padding: 20px 24px;
    margin: 14px 0;
}

.goal-card h3 {
    margin: 6px 0 6px;
    color: #102b4d;
}

.goal-card p {
    margin: 0;
    color: #3a4d68;
}

.term-card {
    background: #f4f9f1;
    border: 1px solid #cfe3c6;
    border-radius: 16px;
    padding: 16px 20px;
    margin: 8px 0;
}

.term-card b {
    color: #24521a;
}

.term-card p {
    margin: 6px 0 0;
    color: #3d4b38;
    font-size: .92rem;
}

.case-card {
    background: #ffffff;
    border-left: 5px solid #174d82;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
    box-shadow: 0 4px 14px rgba(24,48,80,.07);
}

.case-card p {
    margin: 6px 0 0;
    color: #3a4d68;
    font-size: .92rem;
}

.reason-card {
    background: rgba(255,255,255,.96);
    border: 1px solid #dbe4ef;
    border-radius: 16px;
    padding: 14px 18px;
    margin: 8px 0;
}

.reason-card p {
    margin: 4px 0 0;
    color: #3a4d68;
    font-size: .92rem;
}

.reason-card .meta {
    color: #718096;
    font-size: .78rem;
}

.event-card {
    background: linear-gradient(135deg, #fff4f2, #fff9ec);
    border: 1px solid #f2b8ae;
    border-left: 6px solid #d9483b;
    border-radius: 18px;
    padding: 18px 24px;
    margin: 12px 0;
}

.event-card h3 {
    margin: 8px 0 6px;
    color: #7a1f16;
}

.event-card p {
    margin: 0;
    color: #4a3b38;
}

.big-result {
    text-align: center;
    background: linear-gradient(135deg, #ffffff, #edf5fc);
    border-radius: 26px;
    padding: 42px 28px;
    border: 1px solid #d7e3ef;
    box-shadow: 0 14px 40px rgba(18,46,80,.1);
}

.big-result .emoji {
    font-size: 4rem;
}

.big-result h1 {
    color: #102b4d;
}

.analysis {
    background: #102b4d;
    color: white;
    padding: 28px;
    border-radius: 22px;
    margin-top: 20px;
}

.analysis h3 {
    color: white;
}

.think {
    background: #fff9e9;
    border: 1px solid #f1dfaa;
    padding: 24px;
    border-radius: 20px;
    margin-top: 18px;
}

.small-note {
    color: #718096;
    font-size: .8rem;
}

div.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    min-height: 46px;
}

div.stButton > button[kind="primary"] {
    background: #174d82;
    border: none;
}

.progress-label {
    color: #607089;
    font-size: .85rem;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ---------- 모션 ---------- */
@keyframes riseIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes popIn { from { opacity: 0; transform: scale(.92); } to { opacity: 1; transform: scale(1); } }
@keyframes floaty { 0%, 100% { transform: translateY(0) rotate(-3deg); } 50% { transform: translateY(-10px) rotate(3deg); } }
@keyframes bounceIn { 0% { transform: scale(.3); } 55% { transform: scale(1.18); } 100% { transform: scale(1); } }
@keyframes ring { 0% { box-shadow: 0 0 0 0 rgba(217,72,59,.45); } 100% { box-shadow: 0 0 0 14px rgba(217,72,59,0); } }
@keyframes glow {
    0%, 100% { box-shadow: 0 8px 24px rgba(24,48,80,.10), 0 0 0 0 rgba(23,77,130,.25); }
    50% { box-shadow: 0 10px 28px rgba(24,48,80,.16), 0 0 0 7px rgba(23,77,130,.12); }
}

.card, .goal-card, .term-card, .case-card, .reason-card, .analysis, .think {
    animation: riseIn .45s ease backwards;
    animation-delay: calc(var(--i, 0) * .09s);
}

.hero { animation: popIn .6s ease backwards; }
.big-result { animation: popIn .6s cubic-bezier(.2, 1.2, .3, 1) backwards; }
.big-result .emoji { display: inline-block; animation: bounceIn .9s ease .25s backwards; }
.event-card { animation: riseIn .45s ease backwards, ring 1.1s ease-out .4s 2; }
.event-card .badge { animation: ring 1.1s ease-out .4s 3; }
.globe { display: inline-block; animation: floaty 3.6s ease-in-out infinite; }
.card.selected { animation: riseIn .45s ease backwards, glow 2.6s ease-in-out infinite; }

.card, .case-card, .term-card { transition: transform .2s ease, box-shadow .2s ease; }
.card:hover { transform: translateY(-4px); box-shadow: 0 16px 36px rgba(24,48,80,.16); }
.case-card:hover, .term-card:hover { transform: translateX(4px); }

div.stButton > button { transition: transform .15s ease, box-shadow .15s ease; }
div.stButton > button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(24,48,80,.18); }
div.stButton > button:active:not(:disabled) { transform: translateY(0); }

@media (max-width: 700px) {
    .hero {
        padding: 34px 20px 30px;
    }
    .hero h1 {
        font-size: 2.15rem;
        letter-spacing: 1.5px;
        white-space: normal;
    }
    .country-card {
        height: auto;
        min-height: 235px;
        overflow: visible;
    }
}

/* 움직임 줄이기 설정을 켠 사용자는 애니메이션 끄기 */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation: none !important;
        transition: none !important;
    }
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# 공통 헤더
# =====================================================
step = st.session_state.game["step"]


def apply_background(step):
    """모든 단계에 같은 배경 (처음의 연한 하늘색 + 아주 옅은 격자 무늬)"""
    grid = ("linear-gradient(rgba(23,77,130,.035) 1px, transparent 1px), "
            "linear-gradient(90deg, rgba(23,77,130,.035) 1px, transparent 1px)")
    st.markdown(
        f"<style>.stApp {{ background-color: #f5f8fc !important; background-image: {grid} !important; "
        f"background-size: 44px 44px !important; }} "
        f"header[data-testid='stHeader'] {{ background: transparent !important; }}</style>",
        unsafe_allow_html=True,
    )


apply_background(step)

if step > 0:
    labels = ["국가 선택", "의제 선택", "입장 확인", "협상 1", "협상 2", "양자 협상", "최종 투표", "결과"]
    idx = max(0, min(step - 1, len(labels) - 1))
    st.markdown(f'<div class="progress-label">DIPLOMATIC SIMULATION · {labels[idx]} · {idx+1}/{len(labels)}</div>', unsafe_allow_html=True)
    st.progress((idx + 1) / len(labels))

# =====================================================
# STEP 0 인트로
# =====================================================
if step == 0:
    st.markdown("""
    <div class="hero">
        <div style="font-size:1rem; color:#a9c7e7; font-weight:700;">UNITED NATIONS · DIPLOMACY SIMULATION</div>
        <div class="globe" style="font-size:3rem; line-height:1; margin:12px 0 4px;">🌎</div>
        <h1>THE GLOBAL TABLE</h1>
        <p>세계의 문제를, 당신의 선택으로.</p>
        <p style="font-size:.95rem;">한 국가의 대표가 되어 협상하고 국제사회의 합의를 이끌어보세요.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card feature-card"><h3>🌐 국제정치</h3><p>국가마다 다른 이해관계를 직접 경험합니다.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card feature-card"><h3>🤝 외교 협상</h3><p>협력과 국익 사이에서 선택합니다.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="card feature-card"><h3>🗳️ 국제회의</h3><p>당신의 선택으로 결의안의 운명이 결정됩니다.</p></div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🌎 회의 참가하기", type="primary", use_container_width=True):
        st.session_state.game["step"] = 1
        st.rerun()

    # ---- 결과 확인 ----
    st.write("")
    with st.expander("📊 결과 확인"):
        pin = st.text_input("PIN 번호", type="password", key="teacher_pin")
        if pin == TEACHER_PIN:
            records = load_results()
            if not records:
                st.info("아직 기록된 결과가 없습니다. 학생들이 끝까지 진행하면 여기에 쌓입니다.")
            else:
                import pandas as pd

                df = pd.DataFrame(records)
                m1, m2, m3 = st.columns(3)
                m1.metric("참여 횟수", len(df))
                m2.metric("결의안 통과율", f"{df['passed'].mean() * 100:.0f}%")
                m3.metric("평균 목표 달성도", f"{df['goal_percent'].mean():.0f}점")

                st.markdown("**외교 전략 유형 분포**")
                style_counts = df["style"].value_counts().reindex(list(RESULT_INFO.keys()), fill_value=0)
                st.bar_chart(style_counts)

                st.markdown("**대표 국가 분포**")
                country_counts = df["country"].value_counts().reindex(list(COUNTRIES.keys()), fill_value=0)
                st.bar_chart(country_counts)

                st.markdown("**의제별 결의안 통과율(%)**")
                agenda_pass = (df.groupby("agenda")["passed"].mean() * 100).round(0)
                st.bar_chart(agenda_pass)

                st.markdown("**최근 기록**")
                st.dataframe(df.tail(20), use_container_width=True)
                st.download_button(
                    "⬇️ CSV로 내려받기",
                    df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="global_table_results.csv",
                    mime="text/csv",
                )

                confirm = st.checkbox("기록을 모두 삭제하겠습니다", key="confirm_clear")
                if st.button("🗑️ 기록 초기화", disabled=not confirm):
                    clear_results()
                    st.rerun()
        elif pin:
            st.error("PIN이 맞지 않습니다.")

# =====================================================
# STEP 1 국가 선택
# =====================================================
elif step == 1:
    st.markdown('<div class="section-title">STEP 1. 대표할 국가를 선택하세요.</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">각 국가는 서로 다른 이해관계와 외교적 우선순위를 가지고 있습니다.</div>', unsafe_allow_html=True)

    country_items = list(COUNTRIES.items())
    for row_start in range(0, len(country_items), 4):
        cols = st.columns(4)
        for col, (name, info) in zip(cols, country_items[row_start:row_start + 4]):
            with col:
                selected = st.session_state.game["country"] == name
                st.markdown(f"""
                <div class="card country-card{' selected' if selected else ''}" style="--i:{list(COUNTRIES).index(name)}; border:2px solid {'#174d82' if selected else '#dbe4ef'};">
                    <div style="font-size:2.4rem;">{info['flag']}</div>
                    <h3>{name}</h3>
                    <span class="badge">외교 관심사</span>
                    <p style="font-size:.85rem;">{info['interest']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("선택" if not selected else "✓ 선택됨", key=f"country_{name}", use_container_width=True):
                    st.session_state.game["country"] = name
                    st.rerun()

    if st.session_state.game["country"]:
        c = st.session_state.game["country"]
        st.info(f"{COUNTRIES[c]['flag']} **{c}**을(를) 대표합니다. {COUNTRIES[c]['desc']}")

    st.markdown('<div class="small-note">※ 국가별 입장은 실제 외교정책을 그대로 반영하지 않는 교육용 단순화입니다.</div>', unsafe_allow_html=True)
    st.write("")
    if st.button("다음 단계 →", type="primary", disabled=st.session_state.game["country"] is None, use_container_width=True):
        st.session_state.game["step"] = 2
        st.rerun()

# =====================================================
# STEP 2 의제
# =====================================================
elif step == 2:
    st.markdown('<div class="section-title">STEP 2. 오늘의 국제 의제를 선택하세요.</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">국제사회가 함께 해결해야 할 문제를 하나 선택합니다.</div>', unsafe_allow_html=True)

    agenda_items = list(AGENDAS.items())
    for row_start in range(0, len(agenda_items), 2):
        cols = st.columns(2)
        for col, (name, info) in zip(cols, agenda_items[row_start:row_start + 2]):
            with col:
                selected = st.session_state.game["agenda"] == name
                st.markdown(f"""
                <div class="card{' selected' if selected else ''}" style="--i:{list(AGENDAS).index(name)}; min-height:210px; border:2px solid {'#174d82' if selected else '#dbe4ef'};">
                    <div style="font-size:3rem;">{info['icon']}</div>
                    <h2>{name}</h2>
                    <p>{info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("이 의제 선택" if not selected else "✓ 선택됨", key=f"agenda_{name}", use_container_width=True):
                    st.session_state.game["agenda"] = name
                    st.rerun()

    st.write("")
    if st.button("다음 단계 →", type="primary", disabled=st.session_state.game["agenda"] is None, use_container_width=True):
        st.session_state.game["step"] = 3
        st.rerun()

# =====================================================
# STEP 3 입장 확인
# =====================================================
elif step == 3:
    agenda = st.session_state.game["agenda"]
    my_country = st.session_state.game["country"]
    st.markdown('<div class="section-title">STEP 3. 국제회의에 앞서 각국의 입장을 확인하세요.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{AGENDAS[agenda]["icon"]} <b>{agenda}</b>에 대한 국가별 이해관계입니다.</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="goal-card">
        <span class="badge">🎯 {COUNTRIES[my_country]['flag']} {my_country}의 이번 회의 목표</span>
        <h3>{COUNTRY_GOALS[agenda][my_country]}</h3>
        <p>협상이 끝난 뒤, 결의안이 이 목표를 얼마나 만족시켰는지 평가합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    render_blocs(my_country)

    cols = st.columns(2)
    items = list(COUNTRIES.keys())
    for i, country in enumerate(items):
        with cols[i % 2]:
            marker = "⭐ 당신이 대표하는 국가" if country == my_country else "국제회의 참가국"
            st.markdown(f"""
            <div class="card">
                <span class="badge">{marker}</span>
                <h3>{COUNTRIES[country]['flag']} {country}</h3>
                <p>{POSITIONS[agenda][country]}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("**📖 협상 전에 알아두면 좋은 용어**")
    for term, definition in GLOSSARY[agenda]:
        st.markdown(f"""
        <div class="term-card">
            <b>{term}</b>
            <p>{definition}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    if st.button("🗣️ 협상 시작", type="primary", use_container_width=True):
        st.session_state.game["step"] = 4
        st.rerun()

# =====================================================
# STEP 4 ROUND 1
# =====================================================
elif step == 4:
    agenda = st.session_state.game["agenda"]
    my_country = st.session_state.game["country"]
    st.markdown('<div class="section-title">ROUND 1 · 핵심 쟁점을 선택하세요.</div>', unsafe_allow_html=True)
    st.caption(f"🎯 나의 목표 ({COUNTRIES[my_country]['flag']} {my_country}): {COUNTRY_GOALS[agenda][my_country]}")

    question, context = QUESTIONS[agenda]
    st.markdown(f'<div class="card"><h2>{question}</h2><p>{context}</p></div>', unsafe_allow_html=True)

    if st.session_state.game["round1"] is None:
        for i, option in enumerate(OPTIONS[agenda]):
            if st.button(f"{chr(65+i)}. {option['title']}", key=f"r1_{i}", use_container_width=True):
                st.session_state.game["round1"] = i
                add_scores(option["scores"])
                st.rerun()
    else:
        selected = OPTIONS[agenda][st.session_state.game["round1"]]
        st.success(f"선택: **{selected['title']}**")
        st.markdown('<div class="card"><h3>🌐 각국의 반응</h3></div>', unsafe_allow_html=True)

        reaction_items = list(zip(COUNTRIES.keys(), selected["reaction"]))
        for row_start in range(0, len(reaction_items), 4):
            reaction_cols = st.columns(4)
            for col, (country, reaction) in zip(reaction_cols, reaction_items[row_start:row_start + 4]):
                with col:
                    st.markdown(f"**{COUNTRIES[country]['flag']} {country}**")
                    st.caption(reaction)

        if st.button("다음 협상으로 →", type="primary", use_container_width=True):
            st.session_state.game["event"] = random.randrange(len(EVENTS[agenda]))
            st.session_state.game["step"] = 5
            st.rerun()

# =====================================================
# STEP 5 ROUND 2
# =====================================================
elif step == 5:
    agenda = st.session_state.game["agenda"]
    my_country = st.session_state.game["country"]
    st.markdown('<div class="section-title">ROUND 2 · 최종 원칙을 선택하세요.</div>', unsafe_allow_html=True)
    st.caption(f"🎯 나의 목표 ({COUNTRIES[my_country]['flag']} {my_country}): {COUNTRY_GOALS[agenda][my_country]}")

    render_event()

    question = "최종 결의안에 어떤 원칙을 포함할까요?"
    st.markdown(f'<div class="card"><h2>{question}</h2><p>국제사회의 합의를 위해 가장 중요하다고 생각하는 원칙을 선택하세요.</p></div>', unsafe_allow_html=True)

    if st.session_state.game["round2"] is None:
        for i, option in enumerate(SECOND_OPTIONS[agenda]):
            if st.button(f"{chr(65+i)}. {option['title']}", key=f"r2_{i}", use_container_width=True):
                st.session_state.game["round2"] = i
                add_scores(option["scores"])
                st.rerun()
    else:
        selected = SECOND_OPTIONS[agenda][st.session_state.game["round2"]]
        st.success(f"선택: **{selected['title']}**")
        render_event_effect()
        if st.button("🤝 양자 협상으로 이동", type="primary", use_container_width=True):
            st.session_state.game["step"] = 6
            st.rerun()

# =====================================================
# STEP 6 ROUND 3 양자 협상
# =====================================================
elif step == 6:
    agenda = st.session_state.game["agenda"]
    my_country = st.session_state.game["country"]
    st.markdown('<div class="section-title">ROUND 3 · 표결 직전, 양자 협상</div>', unsafe_allow_html=True)
    st.caption(f"🎯 나의 목표 ({COUNTRIES[my_country]['flag']} {my_country}): {COUNTRY_GOALS[agenda][my_country]}")

    st.markdown("""
    <div class="card">
        <h2>한 나라를 따로 만나 표를 얻을 수 있습니다.</h2>
        <p>양보하면 상대국의 지지는 올라가지만, 상대국과 반대 진영의 국가들은 불만을 가질 수 있습니다. 또 양보한 만큼 우리나라의 목표는 멀어질 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    render_blocs(my_country)

    if st.session_state.game["round3"] is None:
        deal_idx = st.radio(
            "협상 방식을 선택하세요.",
            options=[0, 1, 2],
            index=2,
            format_func=lambda i: DEALS[i]["label"],
            key="r3_deal",
        )
        st.caption(DEALS[deal_idx]["desc"])

        partner = None
        if deal_idx != 2:
            candidates = [c for c in COUNTRIES if c != my_country]

            def partner_label(c):
                _, _, raw = get_country_reactions(c)
                raw += get_event_deltas()[c]
                return f"{COUNTRIES[c]['flag']} {c} · {bloc_of(c)} · 현재 분위기: {mood_of(raw)}"

            partner = st.selectbox("협상 상대국", candidates, format_func=partner_label, key="r3_partner")
            st.caption(f"💬 {partner}의 입장: {POSITIONS[agenda][partner]}")

        if st.button("🤝 협상 확정", type="primary", use_container_width=True):
            st.session_state.game["round3"] = {"deal": deal_idx, "partner": partner}
            add_scores(DEALS[deal_idx]["scores"])
            st.rerun()
    else:
        r3 = st.session_state.game["round3"]
        deltas = get_deltas()
        if r3["deal"] == 2:
            st.info("양자 협상 없이 기존 입장을 유지했습니다. 모든 국가가 기존 입장 그대로 표결에 들어갑니다.")
        else:
            partner = r3["partner"]
            st.success(f"{COUNTRIES[partner]['flag']} **{partner}**와(과) 협상했습니다 — {DEALS[r3['deal']]['label']}")
            upset = [c for c, d in deltas.items() if d < 0 and c != my_country]
            if upset:
                names = ", ".join(f"{COUNTRIES[c]['flag']} {c}" for c in upset)
                st.warning(f"반대 진영의 불만: {names}")
            if deltas[my_country] < 0:
                st.warning("양보의 대가로 우리나라의 목표 달성도가 일부 줄어듭니다.")
        if st.button("🗳️ 최종 투표로 이동", type="primary", use_container_width=True):
            st.session_state.game["step"] = 7
            st.rerun()

# =====================================================
# STEP 7 FINAL VOTE
# =====================================================
elif step == 7:
    agenda = st.session_state.game["agenda"]
    my_country = st.session_state.game["country"]
    s = st.session_state.game["scores"]
    r2 = SECOND_OPTIONS[agenda][st.session_state.game["round2"]]

    total = len(COUNTRIES)          # 참가국 수 (7)
    majority = total // 2 + 1       # 과반 (4)

    # 투표 모델: 두 라운드의 반응 점수 합 + 타협 보너스 + 양자 협상 영향
    bonus = 1 if s["compromise"] >= 3 else 0
    deltas = get_deltas()
    ev_deltas = get_event_deltas()

    votes = {}
    for country in COUNTRIES:
        _, _, raw = get_country_reactions(country)
        score = raw + bonus + deltas[country] + ev_deltas[country]
        if score >= 1:
            votes[country] = "찬성"
        elif score == 0:
            votes[country] = "기권"
        else:
            votes[country] = "반대"

    yes_count = sum(1 for v in votes.values() if v == "찬성")
    abstain_count = sum(1 for v in votes.values() if v == "기권")
    no_count = sum(1 for v in votes.values() if v == "반대")
    passed = yes_count >= majority

    st.markdown('<div class="section-title">FINAL VOTE</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">당신이 선택한 외교 전략을 국제사회가 평가합니다.</div>', unsafe_allow_html=True)

    principle = r2["title"].rstrip(".")
    resolution = f"국제사회는 '{principle}'라는 원칙을 바탕으로 {RESOLUTION_TAIL[agenda]}"
    st.markdown(f'<div class="card"><span class="badge">PROPOSED RESOLUTION</span><h2>{resolution}</h2></div>', unsafe_allow_html=True)

    display_order = list(COUNTRIES.keys())
    for row_start in range(0, len(display_order), 4):
        cols = st.columns(4)
        for col, country in zip(cols, display_order[row_start:row_start + 4]):
            with col:
                mine = "⭐ " if country == my_country else ""
                st.markdown(f"<div class='card vote-card' style='text-align:center; --i:{display_order.index(country)}'><div style='font-size:1.6rem'>{COUNTRIES[country]['flag']}</div><b>{mine}{country}</b><br>{vote_icon(votes[country])} {votes[country]}</div>", unsafe_allow_html=True)

    ev = get_event()
    if ev:
        st.caption(f"⚡ 이번 회의의 돌발 상황: {ev['title']}")

    if bonus:
        st.caption("🤝 협상에서 보여준 타협 전략 덕분에 일부 국가가 입장을 한 단계 누그러뜨렸습니다.")

    if passed:
        st.success(f"🎉 **결의안 통과!** 찬성 {yes_count} · 기권 {abstain_count} · 반대 {no_count} (총 {total}개국, 과반 {majority}개국)")
    else:
        st.error(f"❌ **결의안 부결** 찬성 {yes_count} · 기권 {abstain_count} · 반대 {no_count} (총 {total}개국, 과반 {majority}개국)")

    # 진영별 표결
    st.markdown("### 🧭 진영별 표결")
    bloc_cols = st.columns(len(BLOCS))
    bloc_yes = {}
    for col, (name, members) in zip(bloc_cols, BLOCS.items()):
        yes_in_bloc = sum(1 for m in members if votes[m] == "찬성")
        bloc_yes[name] = yes_in_bloc
        with col:
            st.metric(name, f"찬성 {yes_in_bloc}/{len(members)}")

    adv = bloc_yes["선진국 연대"]
    dev = bloc_yes["개도국 연대"]
    if adv >= 2 and dev >= 2:
        bloc_msg = "선진국 연대와 개도국 연대가 모두 대체로 찬성했습니다. 진영을 넘어선 폭넓은 합의입니다."
    elif adv >= 2 and dev <= 1:
        bloc_msg = "선진국 연대는 찬성 쪽, 개도국 연대는 반대·유보 쪽으로 기울었습니다. 선진국과 개도국 사이의 입장 차가 드러난 표결입니다."
    elif adv <= 1 and dev >= 2:
        bloc_msg = "개도국 연대는 찬성 쪽, 선진국 연대는 반대·유보 쪽으로 기울었습니다. 책임을 지게 된 선진국의 부담이 쟁점이 된 표결입니다."
    else:
        bloc_msg = "두 진영 모두 지지가 부족했습니다. 어느 쪽의 이해관계도 충분히 담지 못한 결의안이었습니다."
    st.info(bloc_msg)

    # 투표 이유
    st.markdown("### 🗒️ 각국은 왜 이렇게 투표했을까?")
    for country in display_order:
        vote = votes[country]
        r1_react, r2_react, _ = get_country_reactions(country)
        mine = " ⭐" if country == my_country else ""
        delta = deltas[country]
        if delta > 0:
            delta_note = f" · 🤝 양자 협상 효과 +{delta}"
        elif delta < 0:
            delta_note = f" · ⚠️ 양자 협상 영향 {delta}"
        else:
            delta_note = ""
        ev_d = ev_deltas[country]
        if ev_d:
            delta_note += f" · ⚡ 돌발 상황 {ev_d:+d}"
        st.markdown(f"""
        <div class="reason-card" style="--i:{display_order.index(country)}">
            <b>{COUNTRIES[country]['flag']} {country}{mine}</b> · {vote_icon(vote)} {vote}
            <p>{VOTE_REASONS[agenda][country][vote]}</p>
            <div class="meta">1라운드 선택에 대한 반응: {r1_react} · 2라운드 선택에 대한 반응: {r2_react}{delta_note}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("📊 나의 외교 전략 분석하기", type="primary", use_container_width=True):
        st.session_state.game["passed"] = passed
        st.session_state.game["votes"] = votes
        st.session_state.game["yes_count"] = yes_count
        st.session_state.game["step"] = 8
        st.rerun()

# =====================================================
# STEP 8 RESULT
# =====================================================
elif step == 8:
    g = st.session_state.game
    result = get_result()
    emoji, desc, theory = RESULT_INFO[result]
    s = g["scores"]
    agenda = g["agenda"]
    my_country = g["country"]
    passed = g.get("passed", False)
    votes = g.get("votes", {})
    deltas = get_deltas()
    ev_deltas = get_event_deltas()
    ev = get_event()

    # 내 국가의 목표 달성도
    r1_react, r2_react, base_raw = get_country_reactions(my_country)
    goal_raw = base_raw + deltas[my_country] + ev_deltas[my_country]
    goal_percent = goal_percent_of(goal_raw)

    if goal_raw >= 3:
        verdict, verdict_icon = "목표 달성", "🎯"
    elif goal_raw >= 1:
        verdict, verdict_icon = "부분 달성", "🟡"
    else:
        verdict, verdict_icon = "목표 미달성", "⚠️"

    # 수업용 기록 (한 판에 한 번만)
    if not g.get("logged"):
        try:
            save_result({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "country": my_country,
                "agenda": agenda,
                "style": result,
                "passed": bool(passed),
                "goal_percent": goal_percent,
                "round1": g["round1"],
                "round2": g["round2"],
                "deal": g["round3"]["deal"] if g.get("round3") else 2,
                "event": ev["title"] if ev else "",
            })
        except Exception:
            pass
        g["logged"] = True

    st.markdown(f"""
    <div class="big-result">
        <div class="emoji">{emoji}</div>
        <div class="small-note">YOUR DIPLOMATIC STYLE</div>
        <h1>{result}</h1>
        <p>{desc}</p>
    </div>
    """, unsafe_allow_html=True)

    if passed and goal_raw >= 1:
        insight = "결의안도 통과되었고, 우리나라의 목표도 어느 정도 지켜졌습니다. 국제 합의와 국익을 함께 얻은 협상이었습니다."
    elif passed:
        insight = "결의안은 통과했지만 우리나라의 목표는 충분히 반영되지 못했습니다. 합의를 위해 국익을 양보한 셈입니다."
    elif goal_raw >= 1:
        insight = "우리나라의 목표에는 가까웠지만 결의안은 통과되지 못했습니다. 내 입장만 챙기면 국제적 합의를 얻기 어려울 수 있습니다."
    else:
        insight = "결의안도 부결되었고 우리나라의 목표도 지켜지지 못했습니다. 다른 국가들의 이해관계를 더 살폈다면 결과가 달라졌을지 생각해 보세요."

    cost_note = " (양자 협상에서의 양보 비용 반영)" if deltas[my_country] < 0 else ""
    if ev_deltas[my_country]:
        cost_note += f" (돌발 상황 영향 {ev_deltas[my_country]:+d} 반영)"

    st.write("")
    st.markdown(f"""
    <div class="goal-card">
        <span class="badge">🎯 {COUNTRIES[my_country]['flag']} {my_country}의 목표 달성도</span>
        <h3>{COUNTRY_GOALS[agenda][my_country]}</h3>
        <p><b>{verdict_icon} {verdict}</b> · 1라운드 반응: {r1_react} · 2라운드 반응: {r2_react}{cost_note}</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(goal_percent / 100)
    st.caption(f"목표 달성도 {goal_percent}/100 · {insight}")

    st.write("")
    st.markdown("### 📊 외교 전략 지표")

    metrics = [
        ("🤝 국제협력", score_percent(s["cooperation"])),
        ("🛡️ 국익중시", score_percent(s["national"])),
        ("🌐 다자주의", score_percent(s["multi"])),
        ("⚖️ 타협능력", score_percent(s["compromise"])),
    ]

    for label, value in metrics:
        st.write(f"**{label}** · {value}/100")
        st.progress(value / 100)

    st.markdown(f"""
    <div class="analysis">
        <h3>📚 정치외교학적으로 바라보기</h3>
        <p>{theory}</p>
        <p>이번 시뮬레이션에서는 <b>국익, 국제협력, 다자주의, 타협</b> 사이의 선택이 서로 다른 결과를 만들어냈습니다. 실제 국제정치에서도 국가는 자국의 이해관계와 국제사회의 공동 목표 사이에서 끊임없이 조정하고 협상합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- 실제 사례 연결 ----
    st.write("")
    st.markdown("### 🌏 실제 국제사회와 연결해 보기")
    for title, text in CASES[agenda]:
        st.markdown(f"""
        <div class="case-card">
            <b>{title}</b>
            <p>{text}</p>
        </div>
        """, unsafe_allow_html=True)
    st.caption("※ 교육용 요약입니다. 정확한 내용과 최신 진행 상황은 별도의 자료로 확인해 보세요.")

    # ---- 맞춤형 THINK ABOUT IT ----
    choice_question = THINK_BY_CHOICE[agenda][g["round2"]]
    if passed and goal_raw >= 1:
        follow_up = "결의안도 통과하고 내 목표도 지켜졌다면, 이 합의에 반대한 국가들은 무엇을 포기해야 했을까요?"
    elif passed:
        follow_up = "결의안은 통과했지만 내 목표는 충분히 지켜지지 못했습니다. 합의의 '통과'와 '만족'은 같은 것일까요?"
    elif goal_raw >= 1:
        follow_up = "내 목표에는 가까웠지만 결의안은 부결되었습니다. 합의 없이 내 입장을 지킨 것은 성공일까요?"
    else:
        follow_up = "결의안도 부결되고 목표도 지키지 못했습니다. 어느 지점에서 양보하거나 다른 국가와 손잡았다면 달랐을까요?"

    event_q = f"돌발 상황 '{ev['title']}'이(가) 없었다면, 같은 선택이 같은 결과를 냈을까요?" if ev else ""

    st.markdown(f"""
    <div class="think">
        <h3>💭 THINK ABOUT IT</h3>
        <p><b>{choice_question}</b></p>
        <p>{follow_up}</p>
        <p>{event_q}</p>
        <p>국가의 이익과 국제사회의 공동 이익이 충돌한다면 무엇을 우선해야 할까요?</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- 전체 선택 기록 ----
    st.write("")
    st.markdown("### 📝 나의 선택 기록")
    with st.expander("선택과 각국의 반응 한눈에 보기", expanded=True):
        opt1 = OPTIONS[agenda][g["round1"]]
        opt2 = SECOND_OPTIONS[agenda][g["round2"]]
        names = list(COUNTRIES.keys())

        def reaction_line(reactions):
            return " · ".join(f"{COUNTRIES[n]['flag']} {n} {r}" for n, r in zip(names, reactions))

        st.markdown(f"**대표 국가:** {COUNTRIES[my_country]['flag']} {my_country} · **의제:** {AGENDAS[agenda]['icon']} {agenda}")
        st.markdown(f"**ROUND 1 선택:** {opt1['title']}")
        st.caption(reaction_line(opt1["reaction"]))
        st.markdown(f"**ROUND 2 선택:** {opt2['title']}")
        st.caption(reaction_line(opt2["reaction"]))
        if ev:
            st.markdown(f"**돌발 상황:** ⚡ {ev['title']}")
        r3 = g.get("round3")
        if r3 and r3["deal"] != 2:
            st.markdown(f"**ROUND 3 양자 협상:** {COUNTRIES[r3['partner']]['flag']} {r3['partner']} · {DEALS[r3['deal']]['label']}")
        else:
            st.markdown("**ROUND 3 양자 협상:** 하지 않음")
        vote_line = " · ".join(f"{COUNTRIES[n]['flag']} {n} {vote_icon(votes[n])}{votes[n]}" for n in names if n in votes)
        st.markdown(f"**최종 투표:** {'통과' if passed else '부결'} (찬성 {g.get('yes_count', 0)}개국)")
        st.caption(vote_line)

    # ---- 같은 선택, 다른 입장 / 다른 국가로 다시 해보기 ----
    st.markdown("### 🔁 같은 선택을 다른 국가가 했다면?")
    rows = ["| 국가 | 진영 | 목표 달성도 | 최종 투표 |", "|---|---|---|---|"]
    others = []
    for c in COUNTRIES:
        _, _, raw = get_country_reactions(c)
        pct = goal_percent_of(raw + ev_deltas[c])
        mark = " ⭐" if c == my_country else ""
        v = votes.get(c, "-")
        rows.append(f"| {COUNTRIES[c]['flag']} {c}{mark} | {bloc_of(c)} | {pct}점 | {vote_icon(v) if v != '-' else ''} {v} |")
        if c != my_country:
            others.append((pct, c))
    st.markdown("\n".join(rows))
    st.caption("※ 목표 달성도는 1·2라운드 선택에 대한 각국의 반응과 돌발 상황의 영향을 기준으로 했으며, 양자 협상의 양보 비용은 반영하지 않았습니다.")

    others.sort()
    worst_pct, worst_country = others[0]
    st.markdown(f"같은 선택이라도 **{COUNTRIES[worst_country]['flag']} {worst_country}**를 대표했다면 목표 달성도가 {worst_pct}점으로 가장 낮았을 거예요. 입장이 가장 달랐던 나라의 시선으로 같은 의제를 다시 경험해 보세요.")

    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button(f"{COUNTRIES[worst_country]['flag']} {worst_country}(으)로 다시 해보기", type="primary", use_container_width=True):
            restart_with(worst_country)
    with rc2:
        if st.button("🔄 처음부터 다시 회의하기", use_container_width=True):
            reset_game()

    st.markdown("""
    <div class="small-note" style="margin-top:20px;">
    본 웹사이트는 정치외교학 학습을 위한 모의 국제회의 시뮬레이션입니다.
    실제 UN 의사결정 과정과는 차이가 있으며 교육을 위해 단순화된 모델을 사용합니다.
    </div>
    """, unsafe_allow_html=True)