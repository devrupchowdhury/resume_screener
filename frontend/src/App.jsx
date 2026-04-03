import { useState, useRef } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const colors = {
  bg:      "#0B0F1A",
  surface: "#111827",
  card:    "#1A2235",
  border:  "#2A3548",
  accent:  "#3B82F6",
  green:   "#10B981",
  yellow:  "#F59E0B",
  red:     "#EF4444",
  text:    "#E5E7EB",
  muted:   "#6B7280",
};

const grade_color = (g) => ({A:"#10B981",B:"#3B82F6",C:"#F59E0B",D:"#F97316",F:"#EF4444"}[g] || "#6B7280");

// ── Score bar ─────────────────────────────────────────────
function ScoreBar({ label, value, color }) {
  return (
    <div style={{marginBottom:10}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
        <span style={{fontSize:13,color:colors.muted}}>{label}</span>
        <span style={{fontSize:13,fontWeight:700,color}}>{value.toFixed(1)}</span>
      </div>
      <div style={{height:6,borderRadius:99,background:colors.border}}>
        <div style={{height:"100%",borderRadius:99,width:`${Math.min(value,100)}%`,background:color,transition:"width 0.8s ease"}}/>
      </div>
    </div>
  );
}

// ── Candidate card ────────────────────────────────────────
function CandidateCard({ r, rank }) {
  const [open, setOpen] = useState(false);
  const gc = grade_color(r.grade);
  return (
    <div style={{background:colors.card,border:`1px solid ${colors.border}`,borderRadius:12,marginBottom:12,overflow:"hidden"}}>
      <div
        onClick={()=>setOpen(o=>!o)}
        style={{padding:"16px 20px",cursor:"pointer",display:"flex",alignItems:"center",gap:16}}
      >
        <div style={{width:36,height:36,borderRadius:"50%",background:colors.border,display:"flex",alignItems:"center",justifyContent:"center",fontWeight:700,fontSize:14,color:colors.muted,flexShrink:0}}>
          #{rank}
        </div>
        <div style={{flex:1}}>
          <div style={{fontWeight:700,fontSize:16,color:colors.text}}>{r.candidate_name}</div>
          <div style={{fontSize:13,color:colors.muted}}>{r.email || r.filename}</div>
        </div>
        <div style={{textAlign:"right"}}>
          <div style={{fontSize:24,fontWeight:900,color:gc}}>{r.grade}</div>
          <div style={{fontSize:13,color:colors.muted}}>{r.final_score.toFixed(1)} / 100</div>
        </div>
        <div style={{fontSize:18,color:colors.muted,marginLeft:8}}>{open?"▲":"▼"}</div>
      </div>

      {open && (
        <div style={{padding:"0 20px 20px",borderTop:`1px solid ${colors.border}`}}>
          <div style={{paddingTop:16}}>
            <ScoreBar label="Semantic Match"   value={r.semantic_score}  color="#8B5CF6"/>
            <ScoreBar label="Skill Match"      value={r.skill_score}     color={colors.accent}/>
            <ScoreBar label="Experience"       value={r.experience_score} color={colors.green}/>
            <ScoreBar label="Final Score"      value={r.final_score}     color={gc}/>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginTop:16}}>
            <div>
              <div style={{fontSize:12,fontWeight:700,color:colors.green,marginBottom:6}}>✓ MATCHED SKILLS</div>
              <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
                {(r.matched_skills||[]).map(s=>(
                  <span key={s} style={{background:"rgba(16,185,129,0.15)",color:colors.green,padding:"2px 8px",borderRadius:99,fontSize:12}}>{s}</span>
                ))}
                {!r.matched_skills?.length && <span style={{color:colors.muted,fontSize:12}}>None</span>}
              </div>
            </div>
            <div>
              <div style={{fontSize:12,fontWeight:700,color:colors.red,marginBottom:6}}>✗ MISSING SKILLS</div>
              <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
                {(r.missing_skills||[]).map(s=>(
                  <span key={s} style={{background:"rgba(239,68,68,0.15)",color:colors.red,padding:"2px 8px",borderRadius:99,fontSize:12}}>{s}</span>
                ))}
                {!r.missing_skills?.length && <span style={{color:colors.muted,fontSize:12}}>All matched!</span>}
              </div>
            </div>
          </div>
          <div style={{marginTop:16,background:colors.surface,borderRadius:8,padding:14}}>
            <div style={{fontSize:12,fontWeight:700,color:colors.muted,marginBottom:6}}>EXPLANATION</div>
            <pre style={{fontSize:12,color:colors.text,whiteSpace:"pre-wrap",margin:0,fontFamily:"monospace"}}>{r.explanation}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Step indicator ─────────────────────────────────────────
function Steps({ current }) {
  const steps = ["Post a Job", "Upload Resumes", "View Results"];
  return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:0,marginBottom:36}}>
      {steps.map((s,i)=>(
        <>
          <div key={s} style={{display:"flex",flexDirection:"column",alignItems:"center",gap:6}}>
            <div style={{
              width:32,height:32,borderRadius:"50%",display:"flex",alignItems:"center",
              justifyContent:"center",fontWeight:700,fontSize:14,
              background: i <= current ? colors.accent : colors.border,
              color: i <= current ? "#fff" : colors.muted,
              transition:"background 0.3s",
            }}>{i+1}</div>
            <span style={{fontSize:12,color: i===current ? colors.text : colors.muted,whiteSpace:"nowrap"}}>{s}</span>
          </div>
          {i < steps.length-1 && (
            <div key={`line-${i}`} style={{height:2,width:60,background: i < current ? colors.accent : colors.border,marginBottom:20,transition:"background 0.3s"}}/>
          )}
        </>
      ))}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────
export default function App() {
  const [step, setStep]         = useState(0);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  // Step 0: Job form
  const [jobTitle, setJobTitle]   = useState("");
  const [company,  setCompany]    = useState("");
  const [jdText,   setJdText]     = useState("");
  const [jobData,  setJobData]    = useState(null);

  // Step 1: Upload
  const [files,    setFiles]    = useState([]);
  const [jobId,    setJobId]    = useState("");
  const fileRef                 = useRef();

  // Step 2: Results
  const [results,  setResults]  = useState([]);

  const handlePostJob = async () => {
    if (!jobTitle.trim() || !jdText.trim()) { setError("Title and description are required."); return; }
    setLoading(true); setError("");
    try {
      const res = await fetch(`${API}/job`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({title:jobTitle, company, description:jdText}),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setJobId(data.job_id);
      setJobData(data);
      setStep(1);
    } catch(e) { setError(e.message); }
    setLoading(false);
  };

  const handleScreen = async () => {
    if (!files.length) { setError("Please upload at least one resume."); return; }
    setLoading(true); setError("");
    try {
      const fd = new FormData();
      fd.append("job_id", jobId);
      files.forEach(f => fd.append("resumes", f));
      const res = await fetch(`${API}/screen`, { method:"POST", body:fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setResults(data.results);
      setStep(2);
    } catch(e) { setError(e.message); }
    setLoading(false);
  };

  const reset = () => {
    setStep(0); setJobTitle(""); setCompany(""); setJdText("");
    setJobData(null); setFiles([]); setResults([]); setJobId(""); setError("");
  };

  return (
    <div style={{minHeight:"100vh",background:colors.bg,fontFamily:"'Inter',sans-serif",color:colors.text,padding:"40px 20px"}}>
      <div style={{maxWidth:760,margin:"0 auto"}}>

        {/* Header */}
        <div style={{textAlign:"center",marginBottom:40}}>
          <div style={{fontSize:36,fontWeight:900,letterSpacing:-1}}>
            <span style={{color:colors.accent}}>AI</span> Resume Screener
          </div>
          <div style={{color:colors.muted,marginTop:6,fontSize:15}}>
            Powered by Sentence Transformers · 90%+ Accuracy
          </div>
        </div>

        <Steps current={step}/>

        {error && (
          <div style={{background:"rgba(239,68,68,0.1)",border:`1px solid ${colors.red}`,color:colors.red,padding:"12px 16px",borderRadius:8,marginBottom:20,fontSize:14}}>
            ⚠ {error}
          </div>
        )}

        {/* ── STEP 0: Post Job ── */}
        {step === 0 && (
          <div style={{background:colors.card,border:`1px solid ${colors.border}`,borderRadius:16,padding:28}}>
            <h2 style={{margin:"0 0 20px",fontSize:20}}>Post a Job Description</h2>
            <label style={{fontSize:13,color:colors.muted}}>Job Title *</label>
            <input value={jobTitle} onChange={e=>setJobTitle(e.target.value)}
              placeholder="e.g. Senior ML Engineer"
              style={{width:"100%",boxSizing:"border-box",padding:"10px 14px",background:colors.surface,border:`1px solid ${colors.border}`,borderRadius:8,color:colors.text,fontSize:15,marginTop:6,marginBottom:16,outline:"none"}}/>
            <label style={{fontSize:13,color:colors.muted}}>Company Name</label>
            <input value={company} onChange={e=>setCompany(e.target.value)}
              placeholder="e.g. Google"
              style={{width:"100%",boxSizing:"border-box",padding:"10px 14px",background:colors.surface,border:`1px solid ${colors.border}`,borderRadius:8,color:colors.text,fontSize:15,marginTop:6,marginBottom:16,outline:"none"}}/>
            <label style={{fontSize:13,color:colors.muted}}>Job Description *</label>
            <textarea value={jdText} onChange={e=>setJdText(e.target.value)}
              rows={8} placeholder="Paste the full job description here..."
              style={{width:"100%",boxSizing:"border-box",padding:"10px 14px",background:colors.surface,border:`1px solid ${colors.border}`,borderRadius:8,color:colors.text,fontSize:14,marginTop:6,marginBottom:20,resize:"vertical",outline:"none"}}/>
            <button onClick={handlePostJob} disabled={loading}
              style={{width:"100%",padding:"12px",background:colors.accent,color:"#fff",border:"none",borderRadius:8,fontWeight:700,fontSize:16,cursor:"pointer",opacity:loading?0.6:1}}>
              {loading ? "Analyzing JD..." : "→ Analyze & Continue"}
            </button>
          </div>
        )}

        {/* ── STEP 1: Upload ── */}
        {step === 1 && (
          <div>
            <div style={{background:colors.card,border:`1px solid ${colors.border}`,borderRadius:16,padding:24,marginBottom:16}}>
              <div style={{fontSize:13,color:colors.muted,marginBottom:4}}>Job ID: <code style={{color:colors.accent}}>{jobId}</code></div>
              <div style={{fontSize:16,fontWeight:700}}>{jobTitle} {company && `@ ${company}`}</div>
              <div style={{marginTop:12}}>
                <div style={{fontSize:12,color:colors.muted,marginBottom:6}}>REQUIRED SKILLS DETECTED ({jobData?.required_skills?.length})</div>
                <div style={{display:"flex",flexWrap:"wrap",gap:6}}>
                  {(jobData?.required_skills||[]).map(s=>(
                    <span key={s} style={{background:"rgba(59,130,246,0.15)",color:colors.accent,padding:"3px 10px",borderRadius:99,fontSize:12}}>{s}</span>
                  ))}
                </div>
              </div>
            </div>

            <div style={{background:colors.card,border:`1px solid ${colors.border}`,borderRadius:16,padding:28}}>
              <h2 style={{margin:"0 0 20px",fontSize:20}}>Upload Resumes</h2>
              <div
                onClick={()=>fileRef.current.click()}
                style={{border:`2px dashed ${colors.border}`,borderRadius:12,padding:40,textAlign:"center",cursor:"pointer",marginBottom:16,transition:"border-color 0.2s"}}
                onMouseEnter={e=>e.currentTarget.style.borderColor=colors.accent}
                onMouseLeave={e=>e.currentTarget.style.borderColor=colors.border}
              >
                <div style={{fontSize:32,marginBottom:8}}>📄</div>
                <div style={{color:colors.muted}}>Click to upload <strong style={{color:colors.text}}>PDF or DOCX</strong> resumes</div>
                <div style={{color:colors.muted,fontSize:12,marginTop:4}}>Multiple files supported</div>
                <input ref={fileRef} type="file" multiple accept=".pdf,.docx,.doc,.txt" style={{display:"none"}}
                  onChange={e=>setFiles(Array.from(e.target.files))}/>
              </div>

              {files.length > 0 && (
                <div style={{marginBottom:20}}>
                  {files.map(f=>(
                    <div key={f.name} style={{display:"flex",alignItems:"center",gap:10,padding:"8px 12px",background:colors.surface,borderRadius:8,marginBottom:6}}>
                      <span style={{color:colors.accent}}>📋</span>
                      <span style={{flex:1,fontSize:14}}>{f.name}</span>
                      <span style={{fontSize:12,color:colors.muted}}>{(f.size/1024).toFixed(0)} KB</span>
                    </div>
                  ))}
                </div>
              )}

              <div style={{display:"flex",gap:12}}>
                <button onClick={()=>setStep(0)} style={{flex:1,padding:"12px",background:"transparent",color:colors.muted,border:`1px solid ${colors.border}`,borderRadius:8,fontWeight:600,cursor:"pointer"}}>
                  ← Back
                </button>
                <button onClick={handleScreen} disabled={loading}
                  style={{flex:2,padding:"12px",background:colors.accent,color:"#fff",border:"none",borderRadius:8,fontWeight:700,fontSize:16,cursor:"pointer",opacity:loading?0.6:1}}>
                  {loading ? "Screening resumes..." : `Screen ${files.length} Resume${files.length!==1?"s":""}`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 2: Results ── */}
        {step === 2 && (
          <div>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20}}>
              <div>
                <h2 style={{margin:0,fontSize:22}}>Screening Results</h2>
                <div style={{color:colors.muted,fontSize:14,marginTop:2}}>{results.length} candidate{results.length!==1?"s":""} ranked</div>
              </div>
              <button onClick={reset} style={{padding:"8px 16px",background:"transparent",color:colors.accent,border:`1px solid ${colors.accent}`,borderRadius:8,fontWeight:600,cursor:"pointer",fontSize:14}}>
                + New Job
              </button>
            </div>

            {/* Summary bar */}
            <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:12,marginBottom:20}}>
              {["A","B","C"].map(g=>{
                const count = results.filter(r=>r.grade===g).length;
                return (
                  <div key={g} style={{background:colors.card,border:`1px solid ${colors.border}`,borderRadius:12,padding:"14px 16px",textAlign:"center"}}>
                    <div style={{fontSize:28,fontWeight:900,color:grade_color(g)}}>{count}</div>
                    <div style={{fontSize:13,color:colors.muted}}>Grade {g}</div>
                  </div>
                );
              })}
            </div>

            {results.map((r,i)=>(
              <CandidateCard key={r._id||i} r={r} rank={i+1}/>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
