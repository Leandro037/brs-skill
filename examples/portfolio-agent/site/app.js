const state = {
  data: null,
  index: 0,
  editing: false
};

const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];

async function loadData(){
  const saved = localStorage.getItem("brsPortfolioData");
  if(saved){
    try { state.data = JSON.parse(saved); render(); return; } catch {}
  }
  const res = await fetch("./portfolio.json");
  state.data = await res.json();
  render();
}

function getPath(obj,path){ return path.split(".").reduce((o,k)=>o?.[k],obj); }
function setPath(obj,path,value){
  const keys=path.split(".");
  const last=keys.pop();
  const target=keys.reduce((o,k)=>o[k],obj);
  target[last]=value;
}

function render(){
  $$("[data-path]").forEach(el=>{
    const v=getPath(state.data,el.dataset.path);
    if(v!==undefined) el.textContent=v;
  });

  $("#stats").innerHTML=state.data.stats.map(s=>`
    <div class="stat"><strong>${escapeHtml(s.value)}</strong><span>${escapeHtml(s.label)}</span></div>`).join("");

  $("#skills").innerHTML=state.data.skills.map(x=>`<span class="skill">${escapeHtml(x)}</span>`).join("");

  $("#timeline").innerHTML=state.data.experience.map(x=>`
    <article class="timeline-item reveal visible">
      <div class="timeline-period">${escapeHtml(x.period)}</div>
      <div class="timeline-role"><strong>${escapeHtml(x.role)}</strong><span>${escapeHtml(x.company)}</span></div>
      <div class="timeline-text">${escapeHtml(x.text)}</div>
    </article>`).join("");

  $("#contactLinks").innerHTML=state.data.contact.links.map(x=>`
    <a class="magnetic" href="${attr(x.url)}" target="_blank" rel="noreferrer">${escapeHtml(x.label)} ↗</a>`).join("");

  renderProjects();
  enableMagnetic();
}

function renderProjects(){
  const track=$("#projectTrack");
  track.innerHTML=state.data.projects.map((p,i)=>`
    <article class="project-card ${i===state.index?"active":""}" data-card="${i}">
      <span class="project-tag">${escapeHtml(p.tag)}</span>
      <h3>${escapeHtml(p.title)}</h3>
      <p>${escapeHtml(p.description)}</p>
      <div class="project-bottom">
        <div class="project-metric"><strong>${escapeHtml(p.metric)}</strong><span>${escapeHtml(p.metricLabel)}</span></div>
        <a class="project-link" href="${attr(p.link)}" ${p.link.startsWith("http")?'target="_blank" rel="noreferrer"':""} aria-label="Abrir ${attr(p.title)}">↗</a>
      </div>
    </article>`).join("");
  updateCarousel();
  enableTilt();
}

function updateCarousel(){
  const track=$("#projectTrack");
  const card=track.children[0];
  if(!card)return;
  const gap=22;
  const width=card.getBoundingClientRect().width+gap;
  track.style.transform=`translateX(-${state.index*width}px)`;
  [...track.children].forEach((el,i)=>el.classList.toggle("active",i===state.index));
  $("#projectIndex").textContent=`${String(state.index+1).padStart(2,"0")} / ${String(state.data.projects.length).padStart(2,"0")}`;
  const progress=$("#carouselProgressBar");
  if(progress){
    const count=Math.max(1,state.data.projects.length);
    progress.style.width=(100/count)+"%";
    progress.style.transform=`translateX(${state.index*100}%)`;
  }
}

$("#nextProject").addEventListener("click",()=>{state.index=(state.index+1)%state.data.projects.length;updateCarousel()});
$("#prevProject").addEventListener("click",()=>{state.index=(state.index-1+state.data.projects.length)%state.data.projects.length;updateCarousel()});
window.addEventListener("resize",updateCarousel);

function enableTilt(){
  $$(".project-card").forEach(card=>{
    card.addEventListener("pointermove",e=>{
      if(!card.classList.contains("active"))return;
      const r=card.getBoundingClientRect();
      const x=(e.clientX-r.left)/r.width-.5;
      const y=(e.clientY-r.top)/r.height-.5;
      card.style.transform=`perspective(900px) rotateY(${x*5}deg) rotateX(${-y*5}deg) scale(1)`;
    });
    card.addEventListener("pointerleave",()=>card.style.transform="");
  });
}

function enableMagnetic(){
  $$(".magnetic").forEach(el=>{
    if(el.dataset.magnetic)return;
    el.dataset.magnetic="1";
    el.addEventListener("pointermove",e=>{
      const r=el.getBoundingClientRect();
      const x=(e.clientX-(r.left+r.width/2))*.12;
      const y=(e.clientY-(r.top+r.height/2))*.12;
      el.style.transform=`translate(${x}px,${y}px)`;
    });
    el.addEventListener("pointerleave",()=>el.style.transform="");
  });
}

const observer=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{
    if(entry.isIntersecting){
      $$(".reveal",entry.target).forEach((el,i)=>setTimeout(()=>el.classList.add("visible"),i*80));
      const id=entry.target.id;
      $$(".nav a").forEach(a=>a.classList.toggle("active",a.dataset.section===id));
    }
  });
},{threshold:.2});
$$("[data-observe]").forEach(el=>observer.observe(el));

window.addEventListener("scroll",()=>{
  const max=document.documentElement.scrollHeight-innerHeight;
  $("#scrollProgress").style.width=(max?scrollY/max*100:0)+"%";
});

window.addEventListener("pointermove",e=>{
  const g=$("#cursorGlow");
  g.style.left=e.clientX+"px";g.style.top=e.clientY+"px";
});

$("#editBtn").addEventListener("click",()=>{
  state.editing=!state.editing;
  $$(".editable").forEach(el=>el.contentEditable=state.editing?"true":"false");
  $("#editToast").hidden=!state.editing;
  $("#editBtn").textContent=state.editing?"Salir de edición":"Editar";
});

$("#saveLocal").addEventListener("click",()=>{
  $$(".editable[data-path]").forEach(el=>setPath(state.data,el.dataset.path,el.textContent.trim()));
  localStorage.setItem("brsPortfolioData",JSON.stringify(state.data));
  $("#editToast span").textContent="Guardado en este navegador ✓";
  setTimeout(()=>$("#editToast span").textContent="Modo edición activo",1600);
});

$("#resetLocal").addEventListener("click",()=>{
  localStorage.removeItem("brsPortfolioData");
  location.reload();
});

$("#aiBtn").addEventListener("click",()=>$("#aiDialog").showModal());

$("#runAiEdit").addEventListener("click",async()=>{
  const prompt=$("#aiPrompt").value.trim();
  if(!prompt)return;
  const box=$("#aiResult");
  box.hidden=false;box.className="ai-result";box.textContent="Generando propuesta → ejecutando BRS…";
  try{
    const res=await fetch("/api/portfolio/edit",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({prompt,portfolio:state.data})
    });
    const result=await res.json();
    if(result.decision==="RELEASE"){
      state.data=result.artifact;
      localStorage.setItem("brsPortfolioData",JSON.stringify(state.data));
      render();
      box.className="ai-result ok";
      box.textContent=`RELEASE ✓ · ${result.iterations} ronda(s) · ${result.repair_attempts} reparación(es)\n${result.summary||"BRS validó la propuesta completa."}`;
    }else{
      box.className="ai-result fail";
      box.textContent=`BLOCK ✕\n${result.error||result.failed_checks?.join(", ")||"BRS bloqueó el cambio."}`;
    }
  }catch(err){
    box.className="ai-result fail";
    box.textContent="No se pudo conectar al Portfolio Agent. Ejecutá: python -m apps.portfolio_agent";
  }
});

function escapeHtml(v){return String(v).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function attr(v){return escapeHtml(v)}
$("#year").textContent=new Date().getFullYear();

loadData();


let touchStartX=null;
const carouselShell=$(".carousel-shell");
if(carouselShell){
  carouselShell.addEventListener("touchstart",e=>{touchStartX=e.changedTouches[0].clientX},{passive:true});
  carouselShell.addEventListener("touchend",e=>{
    if(touchStartX===null)return;
    const delta=e.changedTouches[0].clientX-touchStartX;
    if(Math.abs(delta)>45){
      state.index = delta<0
        ? (state.index+1)%state.data.projects.length
        : (state.index-1+state.data.projects.length)%state.data.projects.length;
      updateCarousel();
    }
    touchStartX=null;
  },{passive:true});
}

document.addEventListener("keydown",e=>{
  if(!state.data || document.activeElement?.matches("textarea,[contenteditable='true']"))return;
  if(e.key==="ArrowRight"){
    state.index=(state.index+1)%state.data.projects.length;updateCarousel();
  }else if(e.key==="ArrowLeft"){
    state.index=(state.index-1+state.data.projects.length)%state.data.projects.length;updateCarousel();
  }
});

let lastScrollY=0;
window.addEventListener("scroll",()=>{
  const bar=$(".topbar");
  if(!bar)return;
  bar.classList.toggle("scrolled",scrollY>24);
  if(scrollY>lastScrollY && scrollY>180){
    bar.style.transform="translate(-50%,-8px)";
  }else{
    bar.style.transform="translate(-50%,0)";
  }
  lastScrollY=scrollY;
},{passive:true});
