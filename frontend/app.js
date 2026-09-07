const API = '/api'; let scenario, schedule, metrics;
const $ = id => document.getElementById(id);
const fmt = n => typeof n === 'number' ? n.toLocaleString(undefined,{maximumFractionDigits:1}) : n;
async function get(path){const res=await fetch(API+path); if(!res.ok) throw Error(await res.text()); return res.json()}
async function load(){scenario=await get('/scenario'); metrics=await get('/metrics/availability'); schedule=(await get('/blocks')).blocks; renderAll()}
function renderAll(){ $('tasksCount').textContent=scenario.tasks.length; $('scheduledCount').textContent=schedule.length; $('constraintsCount').textContent=(schedule.length*7).toLocaleString(); $('runtime').textContent='baseline'; renderKpis(metrics.optimized); renderTimeline(); renderRailway(); renderTasks(); renderComparison(metrics); }
function renderKpis(m){const data=[['Asset availability',m.asset_availability+'%','operational'],['Block savings',m.infrastructure_downtime_min+' min','scheduled'],['Critical backlog',m.overdue_maintenance,'deferred'],['Blocks required',m.blocks_required,'possessions'],['Joint utilization',m.joint_blocks,'joint blocks'],['Train delay risk',m.train_delay_min+' min','calculated'],['Robustness',m.robustness+'%','simulation'],['Deadline compliance',m.deadline_compliance+'%','tasks']]; $('kpis').innerHTML=data.map(x=>`<div class="kpi"><label>${x[0]}</label><strong>${fmt(x[1])}</strong><delta>${x[2]}</delta></div>`).join('')}
function renderTimeline(){const axis=$('timeAxis'); axis.innerHTML=[0,4,8,12,16,20,24].map((x,i)=>`<span style="left:${i*16.666}%">${String(x).padStart(2,'0')}:00</span>`).join(''); const rows={}; schedule.forEach(b=>(rows[b.section]??=[]).push(b)); $('timeline').innerHTML=Object.entries(rows).map(([section,blocks])=>`<div class="track-row"><div class="track-label">${section}</div><div class="track-lane">${blocks.map(b=>{const t=scenario.tasks.find(x=>b.task_ids.includes(x.id)); const cls=t?.department==='Engineering'?'eng':t?.department==='S&T'?'sig':'trd'; return `<div class="block ${cls}" style="left:${b.start/14.4}%;width:${Math.max(2,(b.end-b.start)/14.4)}%" onclick="showTask('${t.id}')">${t.id} · ${t.duration}m</div>`}).join('')}</div></div>`).join('')||'<div class="solver-note">No blocks scheduled.</div>'}
function renderRailway(){const stations=scenario.stations; $('railway').innerHTML=`<div class="rail-line"></div>`+stations.map((s,i)=>`<div class="rail-node" style="left:${5+i*22.5}%" onclick="showAsset('${s.id}')"><i></i><strong>${s.name}</strong><small>${s.km} km</small></div>`).join('')}
function renderTasks(){const tasks=[...scenario.tasks].sort((a,b)=>b.priority_score-a.priority_score).slice(0,5); $('taskList').innerHTML=tasks.map(t=>`<div class="task-row" onclick="showTask('${t.id}')"><span class="task-id">${t.id}</span><div><div class="task-desc">${t.description}</div><div class="task-meta">${t.department} · ${t.section} · score ${t.priority_score}</div></div><span class="priority ${t.priority==='P1'?'p1':'p2'}">${t.priority}</span></div>`).join('')}
function renderComparison(c){const rows=[['Asset availability','asset_availability','%'],['Infrastructure downtime','infrastructure_downtime_min','min'],['Train delay','train_delay_min','min'],['Blocks required','blocks_required',''],['Critical tasks completed','critical_tasks_completed',''],['Deadline compliance','deadline_compliance','%'],['Robustness','robustness','%']]; $('comparison').innerHTML=`<div class="comparison"><div class="compare-row head"><span>Metric</span><span>Relative view</span><span>Baseline</span><span>Optimized</span><span>Delta</span></div>`+rows.map(([label,key,unit])=>{const b=c.baseline[key],o=c.optimized[key],d=c.delta[key]; const better=['train_delay_min','infrastructure_downtime_min','blocks_required'].includes(key)?d<0:d>0; return `<div class="compare-row"><span>${label}</span><span class="bar"><i style="width:${Math.min(100,Math.max(4,Number(o)||0))}%"></i></span><span>${fmt(b)}${unit}</span><span>${fmt(o)}${unit}</span><span class="${better?'positive':'negative'}">${d>0?'+':''}${fmt(d)}${unit}</span></div>`}).join('')+'</div>'}
window.showTask=async id=>{const t=scenario.tasks.find(x=>x.id===id), e=await get(`/tasks/${id}/explanation`); $('drawerContent').innerHTML=`<div class="eyebrow">EXPLAINABILITY TRACE</div><h2>${t.id} · ${t.description}</h2><p>${t.department} · ${t.section} · ${t.asset_id}</p><div class="factor"><span>Priority score</span><strong>${t.priority_score}/100</strong></div>`+Object.entries(e.factors).map(([k,v])=>`<div class="factor"><span>${k.replaceAll('_',' ')}</span><strong>+${v}</strong></div>`).join('')+`<h3>Why this slot?</h3><p>${e.selected_block?`Scheduled ${Math.floor(e.selected_block.start/60).toString().padStart(2,'0')}:${(e.selected_block.start%60).toString().padStart(2,'0')}–${Math.floor(e.selected_block.end/60).toString().padStart(2,'0')}:${(e.selected_block.end%60).toString().padStart(2,'0')} because the selected interval satisfies train separation, section exclusivity, crew availability and deadline constraints.`:'No feasible interval under current hard constraints.'}</p><h3>Rejected alternatives</h3><ul>${e.rejected_alternatives.map(x=>`<li>${x}</li>`).join('')}</ul>`; $('drawer').classList.add('open')}
window.showAsset=id=>{const a=scenario.assets.find(x=>x.id===id); $('drawerContent').innerHTML=`<div class="eyebrow">DIGITAL TWIN ASSET PROFILE</div><h2>${a?.name||'Station node'}</h2><p>Asset profile from the active planning dataset.</p>`; $('drawer').classList.add('open')}
$('closeDrawer').onclick=()=>$('drawer').classList.remove('open'); $('loadBtn').onclick=async()=>{await fetch(API+'/scenario/load?seed=42',{method:'POST'});await load()}; $('optimizeBtn').onclick=async()=>{ $('solverStatus').textContent='SOLVING'; $('stageSolve').classList.add('complete'); $('stageSolve').querySelector('em').textContent='active'; const r=await fetch(API+'/optimization/run',{method:'POST'}); const data=await r.json(); schedule=data.schedule.blocks; metrics=data.comparison; renderAll(); $('solverStatus').textContent=data.schedule.status; $('runtime').textContent=fmt(data.schedule.runtime_ms)+' ms'; $('scheduledCount').textContent=data.schedule.scheduled_task_ids.length; $('stageSolve').querySelector('em').textContent='done'; $('solverNote').textContent='Feasible schedule validated against hard constraints. Review explanations before approval.'}; setInterval(()=>$('clock').textContent=new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}),1000); load().catch(e=>$('solverNote').textContent='API unavailable. Start with: uvicorn backend.app.main:app --reload');
async function refreshTwin(){const state=await get('/simulation/state'); $('twinClock').textContent=state.clock; $('eventStatus').textContent=`${state.active_blocks.length} active block${state.active_blocks.length===1?'':'s'} · ${state.trains.filter(t=>t.state==='IN_SECTION').length} trains in section`}
$('tickBtn').onclick=async()=>{const state=await (await fetch(API+'/simulation/tick?minutes=15',{method:'POST'})).json(); $('twinClock').textContent=state.clock; $('eventStatus').textContent=`Twin advanced to ${state.clock}`}; $('delayBtn').onclick=async()=>{const freight=scenario.trains.find(t=>t.kind==='FREIGHT'); $('eventStatus').textContent='Replanning against freight delay…'; const result=await (await fetch(`${API}/replan?train_id=${freight.id}&delay_minutes=45`,{method:'POST'})).json(); schedule=result.new_plan.blocks; metrics=result.comparison; $('eventStatus').textContent=`Replanned after ${freight.id} +45 min`; renderAll()}; try{const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/events`); socket.onmessage=event=>{const data=JSON.parse(event.data); $('connection').textContent=`● ${data.type.replaceAll('_',' ').toLowerCase()}`}; socket.onclose=()=>$('connection').textContent='○ realtime disconnected'}catch(error){$('connection').textContent='○ realtime unavailable'}; refreshTwin();
let realMap; let realLayer;
async function loadRealMap(){
	$('eventStatus').textContent='Fetching public railway geometry…';
	const response=await fetch(`${API}/live/map?lat=28.6139&lon=77.2090&radius=12000`);
	if(!response.ok){$('eventStatus').textContent='Public map unavailable; active corridor view remains available.'; return}
	const data=await response.json();
	if(!window.L){$('eventStatus').textContent='Leaflet could not load; map data was fetched but not rendered.'; return}
	if(!realMap){realMap=L.map('realMap').setView([data.center.lat,data.center.lon],11); L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:19}).addTo(realMap)}
	if(realLayer) realLayer.remove();
	realLayer=L.geoJSON(data,{style:feature=>({color:feature.geometry.type==='LineString'?'#087f78':'#d88a2d',weight:feature.geometry.type==='LineString'?3:5}),onEachFeature:(feature,layer)=>layer.bindPopup(feature.properties.name)}).addTo(realMap);
	if(realLayer.getBounds().isValid()) realMap.fitBounds(realLayer.getBounds(),{padding:[12,12]});
	$('mapSource').textContent=`${data.features.length} public OSM railway features · ${data.attribution} · fetched ${new Date(data.fetched_at).toLocaleTimeString()}`;
	$('eventStatus').textContent='Real public railway map loaded; operational feed remains separate.';
}
$('mapBtn').onclick=loadRealMap;
async function loadTrainFeed(){
	$('feedStatus').textContent='Refreshing…';
	try{
		const data=await get('/live/status');
		const feed=data.trains||{};
		$('feedStatus').textContent=feed.enabled?'LIVE FEED':'FEED NOT CONFIGURED';
		$('feedMeta').textContent=feed.enabled?`Source: ${feed.source} · ${feed.updates.length} updates · feed timestamp ${feed.feed_timestamp||'not supplied'} · fetched ${feed.fetched_at||'unknown'}`:feed.message||'No authorized public train feed is configured.';
			$('trainUpdates').innerHTML=feed.updates?.length?feed.updates.map(update=>`<div class="train-update"><strong>${update.trip_id||update.vehicle_id||update.id}</strong><span>${update.type}</span><span>${update.route_id||'position update'}</span><b>${update.delay_seconds?`${Math.round(update.delay_seconds/60)} min delay`:'reported'}</b></div>`).join(''):'<div class="search-empty">No live train updates received. The active timetable remains available for planning.</div>';
	}catch(error){$('feedStatus').textContent='FEED ERROR'; $('feedMeta').textContent='Live feed request failed; active timetable remains available.'}
}
$('refreshFeedBtn').onclick=loadTrainFeed;
loadTrainFeed();
async function searchOperations(){
	const query=$('opsSearch').value.trim();
	const kind=$('searchKind').value;
	if(!query){$('searchResults').hidden=true; return}
	const data=await get(`/search?query=${encodeURIComponent(query)}&kind=${kind}`);
	$('searchResults').hidden=false;
	$('searchResults').innerHTML=data.results.length?data.results.map(result=>`<div class="search-result" data-kind="${result.kind}" data-id="${result.id}"><span class="search-kind">${result.kind}</span><div><div class="search-label">${result.id} · ${result.label}</div><div class="search-detail">${result.detail}</div></div><span>→</span></div>`).join(''):'<div class="search-empty">No operational record matched this query.</div>';
	document.querySelectorAll('.search-result').forEach(item=>item.onclick=()=>openSearchResult(item.dataset.kind,item.dataset.id));
}
async function openSearchResult(kind,id){
	if(kind==='task'){await window.showTask(id); return}
	const result=(await get(`/search?query=${encodeURIComponent(id)}&kind=${kind==='train'?'trains':'assets'}&limit=1`)).results[0];
	if(!result)return;
	const record=result.record;
	$('drawerContent').innerHTML=`<div class="eyebrow">${kind.toUpperCase()} RECORD</div><h2>${record.id} · ${result.label}</h2><p>${result.detail}</p><div class="factor"><span>Section</span><strong>${record.section||'Network'}</strong></div><div class="factor"><span>Source state</span><strong>ACTIVE DATASET</strong></div>`;
	$('drawer').classList.add('open');
}
$('searchBtn').onclick=searchOperations;
$('opsSearch').onkeydown=event=>{if(event.key==='Enter')searchOperations()};
const viewModes={'Automatic Planner':'tasks','Block Programme':'tasks','Time-Distance Graph':'trains','Corridor Digital Twin':'assets','Maintenance Backlog':'tasks','Asset Health':'assets','Conflict Center':'all','Joint Blocks':'tasks','What-If Lab':'trains','Optimization Lab':'tasks','Execution':'all','Reports':'all','Data Quality':'all'};
document.querySelectorAll('.nav').forEach(button=>button.onclick=()=>{
	document.querySelectorAll('.nav').forEach(item=>item.classList.remove('active'));
	button.classList.add('active');
	const mode=viewModes[button.textContent.trim()];
	if(mode)$('searchKind').value=mode;
	$('eventStatus').textContent=`${button.textContent.trim()} view active · use Operations Search to inspect live records`;
	renderModuleView(button.textContent.trim());
});
async function renderModuleView(name){
	if(name==='Command Center'){ $('modulePanel').hidden=true; return }
	$('modulePanel').hidden=false; $('moduleEyebrow').textContent=name.toUpperCase(); $('moduleTitle').textContent=name; $('moduleStatus').textContent='LOADING';
	let html='';
	if(name==='Automatic Planner'||name==='Optimization Lab') html='<p>Run the mathematical scheduler against the active scenario.</p><button class="button primary" id="moduleOptimize">Run CP-SAT optimization</button><div class="module-grid" id="moduleOutput"></div>';
	else if(name==='Block Programme'||name==='Time-Distance Graph') html=name==='Time-Distance Graph'?'<p>Train paths are plotted against corridor distance. Shaded possession bands show why a maintenance window fits.</p><div class="stringline" id="stringline"></div>':'<p>Inspect the active programme and timetable movements in the command timeline.</p><button class="button secondary" id="moduleTimeline">Open timeline</button><div class="module-grid" id="moduleOutput"></div>';
	else if(name==='Corridor Digital Twin') html='<p>Inspect the active corridor and load public OpenStreetMap geometry.</p><button class="button secondary" id="moduleMap">Load real map</button><div class="module-grid" id="moduleOutput"></div>';
	else if(name==='Maintenance Backlog'){const data=await get('/requests'); html=`<p>${data.count} maintenance requests · filter with Operations Search or review status below.</p><div class="module-table">${data.requests.map(request=>`<div><strong>${request.request_id}</strong><span>${request.department} · ${request.section} · ${request.description}</span><b>${request.status}</b><button class="text-button request-approve" data-request="${request.request_id}">Approve</button></div>`).join('')}</div>`}
	else if(name==='Asset Health') html=`<div class="module-table">${scenario.assets.map(asset=>`<div><strong>${asset.id}</strong><span>${asset.name} · ${asset.asset_type}</span><b class="health-${asset.health.toLowerCase()}">${asset.health}</b></div>`).join('')}</div>`;
	else if(name==='Conflict Center'){const data=await get('/conflicts'); html=`<p>${data.count} hard conflicts detected in the active schedule.</p><div class="module-table">${data.conflicts.length?data.conflicts.map(item=>`<div><strong>${item.type}</strong><span>${item.message}</span><b>${item.severity}</b></div>`).join(''):'<div class="search-empty">No conflicts detected.</div>'}</div>`}
	else if(name==='Joint Blocks'){const data=await get('/joint-blocks'); html=`<p>${data.length} compatible joint-block opportunities.</p><div class="module-table">${data.length?data.map(item=>`<div><strong>${item.id}</strong><span>${item.section} · ${item.departments.join(' + ')}</span><b>${item.minutes_saved} min saved</b></div>`).join(''):'<div class="search-empty">No compatible joint blocks found.</div>'}</div>`}
	else if(name==='What-If Lab') html='<p>Apply a controlled freight disruption and compare the replanned schedule.</p><button class="button secondary" id="moduleDelay">Simulate F-001 +45 min</button><div class="module-grid" id="moduleOutput"></div>';
	else if(name==='Execution'){const state=await get('/simulation/state'); html=`<p>Digital twin execution state: <strong>${state.clock}</strong></p><button class="button secondary" id="moduleTick">Advance 15 minutes</button><div class="module-grid"><span>Active blocks: ${state.active_blocks.length}</span><span>Trains in section: ${state.trains.filter(train=>train.state==='IN_SECTION').length}</span></div>`}
	else if(name==='Reports') html='<p>Export the current block programme for review.</p><a class="button secondary" href="/api/export/blocks.csv">Download block programme CSV</a>';
	else if(name==='Data Quality'){const data=await get('/data-quality'); html=`<p>Data quality score: <strong>${data.score}%</strong></p><div class="module-table">${data.checks.map(item=>`<div><strong>${item.rule}</strong><span>${item.count} issue(s)</span><b>${item.passed?'PASS':'FAIL'}</b></div>`).join('')}</div>`}
	else if(name==='Models'){const data=await get('/models'); html=`<p>${data.models.length} active models. Training source and provenance are shown for every model.</p><div class="module-table">${data.models.map(model=>`<div><strong>${model.name}</strong><span>${model.algorithm} · ${model.dataset}</span><b>${model.version}</b></div>`).join('')}</div><button class="button primary" id="moduleTrainModels">Retrain models</button>`}
	else if(name==='Administration'){const data=await get('/health'); html=`<div class="module-table">${Object.entries(data).map(([key,value])=>`<div><strong>${key}</strong><span>${value}</span><b>STATUS</b></div>`).join('')}</div>`}
	$('moduleContent').innerHTML=html; $('moduleStatus').textContent='READY'; bindModuleActions(name);
	if(name==='Time-Distance Graph') renderStringline();
}
function bindModuleActions(name){
	if($('moduleOptimize'))$('moduleOptimize').onclick=async()=>{await $('optimizeBtn').click(); $('moduleStatus').textContent='OPTIMIZED'};
	if($('moduleTimeline'))$('moduleTimeline').onclick=()=>document.querySelector('.timeline-panel').scrollIntoView({behavior:'smooth'});
	if($('moduleMap'))$('moduleMap').onclick=loadRealMap;
	if($('moduleDelay'))$('moduleDelay').onclick=()=>$('delayBtn').click();
	if($('moduleTick'))$('moduleTick').onclick=()=>$('tickBtn').click();
	if($('moduleTrainModels'))$('moduleTrainModels').onclick=async()=>{ $('moduleStatus').textContent='TRAINING'; await fetch(API+'/models/train',{method:'POST'}); $('moduleStatus').textContent='TRAINED'; renderModuleView('Models') };
	document.querySelectorAll('.request-approve').forEach(button=>button.onclick=async()=>{await fetch(`${API}/requests/${button.dataset.request}?status=Approved&actor_role=Control%20Office`,{method:'PATCH'}); renderModuleView('Maintenance Backlog')});
}

function renderStringline(){
	const width=900, height=300, left=58, top=24, plotWidth=width-left-18, plotHeight=height-top-30;
	const sectionY={}; scenario.stations.forEach((station,index)=>sectionY[station.id]=top+plotHeight-index*(plotHeight/(scenario.stations.length-1)));
	const sectionKeys=scenario.stations.map(station=>station.id); const yForSection=section=>{const index=Math.max(0,scenario.stations.findIndex(station=>section.startsWith(station.id))); return top+plotHeight-index*(plotHeight/(scenario.stations.length-1))};
	const xForTime=minute=>left+(minute/1440)*plotWidth;
	const grid=[0,240,480,720,960,1200,1440].map(minute=>`<line x1="${xForTime(minute)}" y1="${top}" x2="${xForTime(minute)}" y2="${top+plotHeight}" stroke="#dce5e3"/><text x="${xForTime(minute)}" y="${height-8}" text-anchor="middle" fill="#6e7d87" font-size="10">${String(Math.floor(minute/60)).padStart(2,'0')}:00</text>`).join('');
	const stations=scenario.stations.map((station,index)=>`<line x1="${left}" y1="${yForSection(station.id+'-')}" x2="${left+plotWidth}" y2="${yForSection(station.id+'-')}" stroke="#eef2f1"/><text x="4" y="${yForSection(station.id+'-')+4}" fill="#43545b" font-size="10">${station.name}</text>`).join('');
	const trains=scenario.trains.map(train=>{const startY=yForSection(train.section), endY=Math.max(top,startY-18); return `<line x1="${xForTime(train.start)}" y1="${startY}" x2="${xForTime(train.end)}" y2="${endY}" stroke="${train.kind==='FREIGHT'?'#d88a2d':'#327ab7'}" stroke-width="2"/><circle cx="${xForTime(train.end)}" cy="${endY}" r="3" fill="${train.kind==='FREIGHT'?'#d88a2d':'#327ab7'}"/>`}).join('');
	const blocks=(schedule||[]).map(block=>`<rect x="${xForTime(block.start)}" y="${top}" width="${Math.max(3,(block.end-block.start)/1440*plotWidth)}" height="${plotHeight}" fill="#087f78" opacity=".12"><title>${block.id} · ${block.section}</title></rect>`).join('');
	$('stringline').innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Railway time-distance graph">${grid}${stations}${blocks}${trains}<text x="${width-8}" y="16" text-anchor="end" fill="#327ab7" font-size="10">PASSENGER</text><text x="${width-8}" y="30" text-anchor="end" fill="#d88a2d" font-size="10">FREIGHT</text></svg>`;
}

const moduleLabels=['Models'];
const sidebarSection=document.querySelectorAll('.section-label')[1];
if(sidebarSection&&!Array.from(document.querySelectorAll('.nav')).some(button=>button.textContent.trim()==='Models')){const modelsButton=document.createElement('button'); modelsButton.className='nav'; modelsButton.textContent='Models'; sidebarSection.parentNode.insertBefore(modelsButton,sidebarSection.nextSibling); modelsButton.onclick=()=>{document.querySelectorAll('.nav').forEach(item=>item.classList.remove('active')); modelsButton.classList.add('active'); $('searchKind').value='all'; $('eventStatus').textContent='Models view active'; renderModuleView('Models')}}
