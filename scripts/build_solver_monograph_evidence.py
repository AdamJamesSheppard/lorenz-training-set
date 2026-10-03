#!/usr/bin/env python3
"""Inventory evidence and generate monograph appendices/figures, never solver data."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/solver_monograph'
OUT = ROOT / 'output/pdf/solver_monograph'

def tex(s):
    return ''.join({'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#',
                    '{':r'\{','}':r'\}','$':r'\$','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(s))

def flatten(obj, prefix=''):
    if isinstance(obj,dict):
        for key,value in obj.items():
            yield from flatten(value,f'{prefix}.{key}' if prefix else key)
    elif isinstance(obj,list):
        if len(obj)<=9 and all(isinstance(x,(str,int,float,bool,type(None))) for x in obj):
            yield prefix,repr(obj)
        else:
            for i,value in enumerate(obj):
                yield from flatten(value,f'{prefix}[{i}]')
    elif isinstance(obj,(str,int,float,bool)):
        yield prefix,obj

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    if '--compact-ledger' in sys.argv:
        ledger=json.loads((DEST/'source_ledger.json').read_text())
        for entry in ledger['inventory']:
            fields=entry.get('decision_fields',{})
            if len(fields)>200:
                entry['decision_fields_omitted']=len(fields)-200
                entry['decision_fields']=dict(list(fields.items())[:200])
        ledger['decision_field_policy']='First 200 selected scalar decision fields per file; omitted counts retained. Full files are identified by hashes, not duplicated.'
        (DEST/'source_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
        render_appendices(ledger)
        return
    if '--render-index-only' in sys.argv:
        render_appendices(json.loads((DEST/'source_ledger.json').read_text()))
        return
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    files=[]
    candidates=[ROOT/p for p in tracked if p]
    candidates += list((ROOT/'runs').rglob('*.json'))
    candidates += list((ROOT/'runs').rglob('*.yaml'))
    candidates += list((ROOT/'runs').rglob('git_commit.txt'))
    for p in sorted(set(candidates)):
        if not p.is_file() or 'solver_monograph' in str(p) or p.stat().st_size>2_000_000:
            continue
        raw=p.read_bytes()
        entry={'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
               'tracked':str(p.relative_to(ROOT)) in tracked}
        if p.suffix=='.json':
            try:
                obj=json.loads(raw)
                vals=list(flatten(obj))
                entry['decision_fields']={k:v for k,v in vals if any(w in k.lower() for w in
                    ('status','decision','certified','authorized','gate','order','density_l1','runtime_seconds','maximum_absolute_mass','mean_relative_l1'))}
                if len(entry['decision_fields'])>200:
                    entry['decision_fields_omitted']=len(entry['decision_fields'])-200
                    entry['decision_fields']=dict(list(entry['decision_fields'].items())[:200])
            except (ValueError,UnicodeDecodeError):
                entry['parse_error']=True
        files.append(entry)
    history=subprocess.check_output(['git','log','--reverse','--date=iso-strict','--format=%h|%ad|%s'],cwd=ROOT).decode().splitlines()
    ledger={'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
            'scope':'All tracked source paths and available small run JSON/YAML; metadata is indexed, not presumed reliable. Large arrays are selectively audited.',
            'decision_field_policy':'First 200 selected scalar decision fields per file; omitted counts retained. Full files are identified by hashes, not duplicated.',
            'inventory':files,'chronology':history,'independent_recomputations':{}}
    volume=384000/(180*216*216)
    domain2=ROOT/'runs/mfem-domain-sensitivity/20261003T143753Z/padding2/mfem/final_q2_subcell_averages.bin'
    domain1=ROOT/'runs/mfem-domain-sensitivity/20261003T113423Z/padding1/mfem/final_q2_subcell_averages.bin'
    a=np.fromfile(domain2,dtype=np.float64).reshape(196,232,232)
    b=np.fromfile(domain1,dtype=np.float64).reshape(188,224,224)
    shell=a.copy();shell[4:-4,4:-4,4:-4]=0
    ledger['independent_recomputations']['second_domain']={'l1':float(np.abs(a[4:-4,4:-4,4:-4]-b).sum()*volume),
        'mass':float(a.sum()*volume),'negative_mass':float(np.maximum(-a,0).sum()*volume),
        'added_shell_mass':float(shell.sum()*volume),'finite':bool(np.isfinite(a).all()),
        'input_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (domain2,domain1)}}
    del a,b,shell
    base=ROOT/'runs/mfem-broader-support/20261002T080644Z/mfem'
    initial=np.fromfile(base/'initial_q2_subcell_averages.bin',dtype=np.float64).reshape(180,216,216)
    final=np.fromfile(base/'final_q2_subcell_averages.bin',dtype=np.float64).reshape(180,216,216)
    ledger['independent_recomputations']['broader_exports']={'initial_mass':float(initial.sum()*volume),
        'final_mass':float(final.sum()*volume),'initial_minimum':float(initial.min()),'final_minimum':float(final.min()),
        'input_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.glob('*averages.bin')}}
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(11,6),layout='constrained')
    spacing=np.array([60/180,80/216,80/216]);bounds=[(-30,30),(-40,40),(-10,70)]
    for row,p in enumerate((initial,final)):
        for col,(i,j,k) in enumerate(((0,1,2),(0,2,1),(1,2,0))):
            joint=p.sum(axis=k)*spacing[k]
            ax=axes[row,col]
            ax.imshow(np.log10(np.maximum(joint.T,1e-12)),origin='lower',extent=(*bounds[i],*bounds[j]),
                      aspect='auto',cmap='viridis',vmin=-10,vmax=-1)
            ax.set_xlabel('xyz'[i]+' (Lorenz coordinate)');ax.set_ylabel('xyz'[j]+' (Lorenz coordinate)')
            ax.set_title(('Initial projected law' if row==0 else 'Forecast t=0.05')+' : '+'xyz'[i]+'xyz'[j])
    fig.suptitle('Saved 3-D density: log10 joint marginal density (floor 1e-12)')
    fig.savefig(OUT/'density_marginals.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    centers=[lo+(np.arange(n)+.5)*h for (lo,hi),n,h in zip(bounds,initial.shape,spacing)]
    for i in range(3):
        marginal_i=initial.sum(axis=tuple(j for j in range(3) if j!=i))*np.prod([spacing[j] for j in range(3) if j!=i])
        marginal_f=final.sum(axis=tuple(j for j in range(3) if j!=i))*np.prod([spacing[j] for j in range(3) if j!=i])
        ax.plot(centers[i],marginal_i,label='xyz'[i]+' initial',ls='--')
        ax.plot(centers[i],marginal_f,label='xyz'[i]+' final')
    ax.set_xlabel('Lorenz coordinate (axes overlaid)');ax.set_ylabel('Marginal probability density');ax.legend(ncol=3)
    fig.tight_layout();fig.savefig(OUT/'marginal_lines.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    axes[0].loglog([1,.5,.25],[5.238e-4,5.418e-4,1.620e-4],'o-')
    axes[0].set_xlabel('Coarser dt / first dt');axes[0].set_ylabel('Adjacent-density L1 difference')
    axes[0].set_title('Four-level startup temporal evidence')
    axes[1].plot([20,30,45,60],[.003047,.002789,.001840,.0008313],'o-')
    axes[1].axhline(.001,color='black',ls='--',label='Original mature gate')
    axes[1].set_xlabel('Uniform x-cell count (y,z scaled)');axes[1].set_ylabel('Mean relative correction');axes[1].legend()
    axes[1].set_title('Mature-state intervention decreases with resolution')
    fig.savefig(OUT/'convergence_evidence.pdf');plt.close(fig)
    (DEST/'source_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
    render_appendices(ledger)
    run_dirs=sorted(set('/'.join(e['path'].split('/')[:3]) for e in files if e['path'].startswith('runs/')))
    print('Inventoried',len(files),'source/compact evidence files;',len(run_dirs),'run directories;',len(history),'commits')
    print(json.dumps(ledger['independent_recomputations'],indent=2))

def render_appendices(ledger):
    files=ledger['inventory']
    history=ledger['chronology']
    lines=[r'\chapter{Source ledger and evidence index}',r'\label{app:ledger}',
       'This index inventories the entire tracked tree and available compact run records. Inventory does not imply that every recorded claim is correct. Primary interpreted evidence is cited in the main chapters. The companion JSON retains SHA256 hashes, sizes, decision fields and exact commit chronology.',
       r'\section{Tracked source and preserved compact records}',r'\small',r'\begin{longtable}{p{.70\textwidth}r}',r'\toprule Source path & Bytes\\\midrule\endhead']
    for entry in files:
        if entry['tracked']:
            lines.append(r'\code{'+entry['path']+'} & '+str(entry['bytes'])+r'\\')
    lines += [r'\bottomrule\end{longtable}\normalsize',r'\section{Run records inspected}',
              'The following distinct run directories have compact records in the ledger. Failed, partial and superseded runs remain visible.',r'\begin{itemize}']
    run_dirs=sorted(set('/'.join(e['path'].split('/')[:3]) for e in files if e['path'].startswith('runs/')))
    lines += [r'\item \code{'+p+'}' for p in run_dirs]
    lines += [r'\end{itemize}',r'\section{Independent recomputation}',
              r'\begin{lstlisting}[basicstyle=\ttfamily\footnotesize]',
              json.dumps(ledger['independent_recomputations']['second_domain'],indent=2),
              r'\end{lstlisting}']
    (DEST/'ledger_appendix.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\chapter{Complete recorded Git chronology}',r'\label{app:git}',
       'Commit dates record when changes were logged. They do not prove when uncommitted experiments ran; immutable run timestamps provide the separate execution chronology.',r'\small',
       r'\begin{longtable}{p{.12\textwidth}p{.20\textwidth}p{.56\textwidth}}',r'\toprule Commit & Recorded date & Purpose\\\midrule\endhead']
    for row in history:
        commit,date,purpose=row.split('|',2)
        lines.append(f'{tex(commit)} & {tex(date[:10])} & {tex(purpose)}'+r'\\')
    lines += [r'\bottomrule\end{longtable}\normalsize']
    (DEST/'history_appendix.tex').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
