import { useState, type FormEvent } from "react";
import type { TargetCountry } from "../shared/meetingTypes";

export interface MeetingFormValues {
  title: string;
  counterpart: string;
  date: string;
  targetCountry: TargetCountry;
  transcript: string;
}

interface MeetingFormProps {
  onSubmit: (values: MeetingFormValues) => void;
  submitting: boolean;
}

const COUNTRY_OPTIONS: { value: TargetCountry; label: string }[] = [
  { value: "US", label: "🇺🇸 미국" },
  { value: "JP", label: "🇯🇵 일본" },
  { value: "CN", label: "🇨🇳 중국" }
];

const today = () => new Date().toISOString().slice(0, 10);

export function MeetingForm({ onSubmit, submitting }: MeetingFormProps) {
  const [values, setValues] = useState<MeetingFormValues>({
    title: "",
    counterpart: "",
    date: today(),
    targetCountry: "US",
    transcript: ""
  });

  const canSubmit = values.transcript.trim().length >= 20 && !submitting;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    onSubmit(values);
  }

  return (
    <form className="meeting-form" onSubmit={handleSubmit}>
      <div className="meeting-form__eyebrow">회의록 리뷰</div>
      <h1 className="meeting-form__title">회의록을 붙여넣고 매너 피드백을 받아보세요</h1>
      <p className="meeting-form__hint">
        Zoom·Google Meet에서 받은 회의록(또는 자막 텍스트)을 그대로 붙여넣으면, 상대 국가의
        비즈니스 문화 기준으로 표현을 검토해드려요.
      </p>

      <div className="meeting-form__row">
        <label className="meeting-form__field">
          <span>회의 제목</span>
          <input
            type="text"
            placeholder="예: Marketing + Sales 킥오프"
            value={values.title}
            onChange={(event) => setValues({ ...values, title: event.target.value })}
          />
        </label>
        <label className="meeting-form__field">
          <span>날짜</span>
          <input
            type="date"
            value={values.date}
            onChange={(event) => setValues({ ...values, date: event.target.value })}
          />
        </label>
      </div>

      <div className="meeting-form__row">
        <label className="meeting-form__field">
          <span>상대방 · 회사</span>
          <input
            type="text"
            placeholder="예: Joseph Miller (ABC Marketing)"
            value={values.counterpart}
            onChange={(event) => setValues({ ...values, counterpart: event.target.value })}
          />
          <small className="meeting-form__field-hint">
            입력하면 이 사람의 발화는 제외하고 내 발화에 대해서만 피드백을 드려요.
          </small>
        </label>
        <label className="meeting-form__field">
          <span>상대방 국가</span>
          <select
            value={values.targetCountry}
            onChange={(event) =>
              setValues({ ...values, targetCountry: event.target.value as TargetCountry })
            }
          >
            {COUNTRY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="meeting-form__field meeting-form__field--transcript">
        <span>회의록 (화자: 대사 형식으로 붙여넣으면 더 잘 인식돼요)</span>
        <textarea
          rows={10}
          placeholder={"Seoyun: Hi, Joe! Nice to finally meet you.\nJoseph: Hi, Seoyun. I'm doing well, thank you."}
          value={values.transcript}
          onChange={(event) => setValues({ ...values, transcript: event.target.value })}
        />
      </label>

      <button className="meeting-form__submit" type="submit" disabled={!canSubmit}>
        {submitting ? "분석하는 중..." : "매너 리뷰 시작하기"}
      </button>
    </form>
  );
}
