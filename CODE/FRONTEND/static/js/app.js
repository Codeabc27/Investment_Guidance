function toggleSidebar(){
  const sidebar=document.getElementById("sidebar");
  if(sidebar) sidebar.classList.toggle("open");
}
function setChat(text){const input=document.getElementById("chatInput");if(input){input.value=text;input.focus();}}
function escapeHtml(text){return String(text??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
function formatMoney(value){return "₹"+Number(value||0).toLocaleString("en-IN",{maximumFractionDigits:0});}
function number(value){const n=Number(value);return Number.isFinite(n)?n:0;}
function parseObject(value){if(!value)return {};if(typeof value==="object")return value;try{return JSON.parse(value)}catch{return {}}}
async function requestJSON(url,options={},timeoutMs=30000){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    const response=await fetch(url,{...options,signal:controller.signal});
    const body=await response.text();let data={};
    if(body){try{data=JSON.parse(body)}catch{if(response.ok)throw new Error("The server returned an invalid response.");}}
    if(!response.ok){const error=new Error(data.message||data.detail||`Request failed (${response.status}).`);error.status=response.status;throw error;}
    return {response,data};
  }catch(error){
    if(error.name==="AbortError")throw new Error("The request timed out. Please try again.");
    if(error instanceof TypeError)throw new Error("Unable to reach the backend. Check that the services are running.");
    throw error;
  }finally{clearTimeout(timer);}
}

function renderGoalProjection(data){
  const el=document.getElementById("goalProjectionChart");if(!el)return;
  const current=number(data.current),target=Math.max(number(data.target),1),monthly=number(data.monthly),years=Math.max(number(data.years),1);
  const width=760,height=165,padX=14,padY=15;
  const points=[];for(let i=0;i<9;i++){const t=years*i/8;points.push({x:t,y:Math.min(current+monthly*12*t,target)});}
  const maxY=Math.max(target,current,1);const minY=0;
  const sx=t=>padX+(t/years)*(width-padX*2);const sy=v=>height-padY-((v-minY)/(maxY-minY))*(height-padY*2);
  const poly=points.map(p=>`${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(" ");
  const area=`${padX},${height-padY} ${poly} ${width-padX},${height-padY}`;
  el.innerHTML=`<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-label="Goal projection"><defs><linearGradient id="goalFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#8db9e8" stop-opacity=".28"/><stop offset="1" stop-color="#8db9e8" stop-opacity="0"/></linearGradient></defs><polygon points="${area}" fill="url(#goalFill)"/><polyline points="${poly}" fill="none" stroke="#9bc5ec" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><line x1="${padX}" y1="${sy(target)}" x2="${width-padX}" y2="${sy(target)}" stroke="rgba(255,255,255,.18)" stroke-dasharray="5 6"/><text x="${width-padX}" y="${Math.max(12,sy(target)-6)}" fill="#b9d2e9" font-size="9" text-anchor="end">Target ${formatMoney(target)}</text><text x="${padX}" y="${height-2}" fill="#a9c7e2" font-size="9">Now</text><text x="${width-padX}" y="${height-2}" fill="#a9c7e2" font-size="9" text-anchor="end">${years} yrs</text></svg>`;
}

function renderBarChart(el,items){
  if(!el)return;
  if(!items.length){el.innerHTML='<div class="chart-empty"><b>No projection data available</b><span>Run the analysis again to generate the scenario values.</span></div>';return;}
  const max=Math.max(...items.map(x=>x.value),1);
  el.innerHTML=`<div class="bar-list">${items.map(item=>{const pct=Math.max(4,(item.value/max)*100);const color=item.name==="optimistic"?"#43aa7d":item.name==="pessimistic"?"#d76d6d":"#5d96dc";return `<div class="bar-row"><span class="bar-label">${escapeHtml(item.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div><span class="bar-value">${formatMoney(item.value)}</span></div>`}).join("")}</div>`;
}
function renderDonut(el,entries){
  if(!el)return;
  if(!entries.length){el.innerHTML='<div class="chart-empty"><b>No allocation data available</b><span>Run the analysis again to generate the allocation.</span></div>';return;}
  const total=entries.reduce((s,x)=>s+x.value,0)||1;
  const colors=["#5d96dc","#43aa7d","#e5a84f","#8a73df","#d76d6d"];
  let cursor=0;const stops=[];entries.forEach((x,i)=>{const start=cursor;cursor+=x.value/total*360;stops.push(`${colors[i%colors.length]} ${start}deg ${cursor}deg`);});
  const gradient=stops.join(",");
  el.innerHTML=`<div class="allocation-wrap"><div class="donut" style="background:conic-gradient(${gradient})"><div class="donut-hole"><div><strong>${Math.round(total)}%</strong><span>allocated</span></div></div></div><div class="legend">${entries.map((x,i)=>`<div class="legend-row"><span class="legend-dot" style="background:${colors[i%colors.length]}"></span><span>${escapeHtml(x.label)}</span><b>${x.value.toFixed(0)}%</b></div>`).join("")}</div></div>`;
}

function normalizeAnalysis(data){
  const envelope=parseObject(data);let source=parseObject(envelope.data||envelope.analysis||envelope);let final=parseObject(source.final_response||source.response||source);let explanation=parseObject(final.explanation||source.explanation);
  const portfolio=parseObject(source.candidate_portfolio||source.portfolio||final.candidate_portfolio||final.strategy||final.portfolio);
  let allocation=parseObject(portfolio.allocation||source.allocation||source.asset_allocation||source.allocations);
  const entries=Object.entries(allocation).map(([label,value])=>({label,value:number(value)})).filter(x=>x.value>0);
  let scenarios=parseObject(source.scenarios||final.scenarios||final.result?.scenarios||explanation.scenarios);
  const scenarioEntries=["expected","optimistic","pessimistic"].map(name=>{const item=parseObject(scenarios[name]);const value=number(item.projected_value);return value?{name,label:name[0].toUpperCase()+name.slice(1),value}:null}).filter(Boolean);
  return {source,final,explanation,portfolio,entries,scenarioEntries};
}

function renderAnalysis(data){
  const n=normalizeAnalysis(data);const {final,explanation,entries,scenarioEntries}=n;
  const summary=final.summary||final.recommendation||explanation.summary||n.source.summary;
  const setText=(id,value)=>{const el=document.getElementById(id);if(el&&value!==undefined&&value!==null)el.textContent=Array.isArray(value)?value.join(" • "):typeof value==="object"?JSON.stringify(value):String(value);};
  setText("summaryText",summary||"Your analysis is complete. Review the calculated allocation and scenario outcomes below.");
  const confidence=final.confidence??n.source.confidence;if(confidence!==undefined){const c=number(confidence);setText("confidenceText",`Confidence ${Math.round((c<=1?c:c/100)*100)}%`);}
  setText("whyText",final.why_this_strategy||final.why||final.reasoning||explanation.why_this_strategy||explanation.reasoning||n.portfolio.rationale);
  setText("riskText",final.key_risks||final.risks||explanation.key_risks||n.portfolio.risks);
  setText("assumptionsText",final.assumptions||explanation.assumptions||n.source.assumptions||"Scenario returns are illustrative assumptions, not guarantees.");
  setText("marketText",final.market_context||final.market_research||n.source.market_context||n.source.market_research||explanation.market_context||"Current market context was unavailable for this run.");
  renderDonut(document.getElementById("allocationChart"),entries);
  renderBarChart(document.getElementById("scenarioChart"),scenarioEntries);
}

function renderWhatIf(data){
  const scenarios=parseObject(data?.scenarios);const items=["expected","optimistic","pessimistic"].map(name=>{const item=parseObject(scenarios[name]);const value=number(item.projected_value);return value?{name,label:name[0].toUpperCase()+name.slice(1),value}:null}).filter(Boolean);renderBarChart(document.getElementById("whatIfChart"),items);
}

async function runAnalysis(){
  const button=document.getElementById("runAnalysis"),message=document.getElementById("analysisMessage"),steps=[...document.querySelectorAll(".agent-step")];if(!button)return;
  button.disabled=true;button.textContent="Running…";if(message)message.innerHTML='<div class="alert warning">Running the workflow. Python is calculating the numbers and Gemini is preparing a concise explanation.</div>';
  steps.forEach((step,i)=>{step.classList.remove("processing","done","failed");const small=step.querySelector("small");if(small)small.textContent=i===0?"Processing":"Waiting";});
  try{const {data}=await requestJSON("/analysis/run",{method:"POST",headers:{"Accept":"application/json"}},100000);if(!data.ok)throw new Error(data.message||"Analysis failed");const contract=normalizeAnalysis(data.data);if(contract.final.status&&contract.final.status!=="complete")throw new Error(contract.final.message||"The analysis did not complete.");
    steps.forEach((step,i)=>{step.classList.remove("processing","failed");step.classList.add("done");const small=step.querySelector("small");if(small)small.textContent="Completed";});
    window.ANALYSIS_DATA=data.data||{};const results=document.getElementById("analysisResults");if(results)results.style.display="block";renderAnalysis(window.ANALYSIS_DATA);if(message)message.innerHTML='<div class="alert success">Analysis completed. The recommendation and scenario results are ready.</div>';button.disabled=false;button.textContent="Refresh analysis";
  }catch(err){steps.forEach(step=>{step.classList.remove("processing");step.classList.add("failed");const small=step.querySelector("small");if(small)small.textContent="Failed";});if(message)message.innerHTML=`<div class="alert error">${escapeHtml(err.message)}</div>`;button.disabled=false;button.textContent="Start analysis";}
}

function initChat(){
  const form=document.getElementById("chatForm");if(!form)return;const input=document.getElementById("chatInput"),messages=document.getElementById("chatMessages");
  form.addEventListener("submit",async event=>{event.preventDefault();const text=input.value.trim();if(!text)return;messages.insertAdjacentHTML("beforeend",`<div class="chat-message user"><b>You</b><p>${escapeHtml(text)}</p></div>`);input.value="";messages.insertAdjacentHTML("beforeend",`<div class="chat-message assistant" id="typing"><b>InvestWise AI</b><p>Thinking…</p></div>`);messages.scrollTop=messages.scrollHeight;
    try{const {data}=await requestJSON("/chat",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"},body:new URLSearchParams({message:text})},30000);const typing=document.getElementById("typing");if(typing)typing.remove();const message=data.message||"No response was returned.";messages.insertAdjacentHTML("beforeend",`<div class="chat-message assistant"><b>InvestWise AI</b><p>${escapeHtml(message)}</p></div>`);}catch(err){const typing=document.getElementById("typing");if(typing)typing.remove();if(err.status===401)window.location.href="/login";messages.insertAdjacentHTML("beforeend",`<div class="chat-message assistant"><b>InvestWise AI</b><p>${escapeHtml(err.message||"Unable to reach the backend.")}</p></div>`);}messages.scrollTop=messages.scrollHeight;});
}

document.addEventListener("DOMContentLoaded",()=>{
  const clock=document.getElementById("pageClock");if(clock){const now=new Date();clock.textContent=now.toLocaleDateString("en-IN",{weekday:"short",day:"2-digit",month:"short"});}
  if(window.DASHBOARD_DATA)renderGoalProjection(window.DASHBOARD_DATA);
  if(window.WHAT_IF_DATA)renderWhatIf(window.WHAT_IF_DATA);
  if(window.ANALYSIS_DATA)renderAnalysis(window.ANALYSIS_DATA);
  initChat();
  document.querySelectorAll(".sidebar a").forEach(link=>link.addEventListener("click",()=>document.getElementById("sidebar")?.classList.remove("open")));
});
