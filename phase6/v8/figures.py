"""Standalone descriptive research figures: SVG/PDF and PNG."""
import csv
import json
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from .prepare import HERE


def rows(name):
    with (HERE/'tables'/name).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))


def save(fig,name):
    fig.tight_layout()
    for extension in ('svg','pdf','png'):fig.savefig(HERE/'figures'/f'{name}.{extension}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def main():
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(9,4));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
    boxes=[(0.2,3,'Original C-like source'),(3.2,3,'SmartParse / panic\nrestricted grammar recovery'),
           (0.2,1,'Original full-C source'),(3.2,1,'GCC / Clang / optional tools\nprivate bounded variants'),
           (6.6,2,'Evidence + provenance\npending human root review')]
    for x,y,text in boxes:
        ax.add_patch(FancyBboxPatch((x,y),2.5,0.8,boxstyle='round,pad=.12',fc='#eef3f8',ec='#365976'))
        ax.text(x+1.25,y+.4,text,ha='center',va='center',fontsize=9)
    for start,end in [((2.8,3.4),(3.05,3.4)),((2.8,1.4),(3.05,1.4)),((5.9,3.4),(6.5,2.6)),((5.9,1.4),(6.5,2.2))]:
        ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#365976'))
    ax.set_title('Separate research components; compiler findings are not CGAR findings')
    save(fig,'figure_1_architecture')
    syntax=rows('table_I_syntax.csv');fig,ax=plt.subplots(figsize=(8,4));x=list(range(len(syntax)))
    ax.bar([i-.18 for i in x],[int(r['author_location_matches']) for r in syntax],.36,label='Author anchor matches')
    ax.bar([i+.18 for i in x],[int(r['author_exact_repairs']) for r in syntax],.36,label='Exact authored repairs')
    ax.set_xticks(x,[r['configuration'] for r in syntax]);ax.set_ylabel('Proposed roots / repairs')
    ax.set_title('Author-created syntax set; human adjudication pending');ax.legend()
    save(fig,'figure_2_syntax')
    comparison=json.loads((HERE/'outputs/root_comparison.json').read_text());sets=comparison['original_sets']
    order=['compiler_gcc6','compiler_clang','extended_baseline','gcc14','cppcheck'];seen=set();totals=[]
    for name in order:seen.update(sets[name]);totals.append(len(seen))
    fig,ax=plt.subplots(figsize=(8,4));ax.step(range(len(order)),totals,where='mid',marker='o')
    ax.set_xticks(range(len(order)),order,rotation=15);ax.set_ylabel('Union of supported author proposals')
    ax.set_title('Incremental original-only frozen matches; not verified detection')
    fig.text(.5,-.03,'Known allowlist/anchor gaps undercount existing evidence; see frozen_matching_limitations.json.',ha='center',fontsize=8)
    save(fig,'figure_3_incremental')
    category=rows('table_III_categories.csv');names=sorted({r['category'] for r in category});fig,ax=plt.subplots(figsize=(9,4))
    width=.15
    for i,config in enumerate(order):
        data={r['category']:int(r['original_supported_proposals']) for r in category if r['configuration']==config}
        ax.bar([j+(i-2)*width for j in range(len(names))],[data.get(n,0) for n in names],width,label=config)
    ax.set_xticks(range(len(names)),names);ax.set_ylabel('Supported author proposals');ax.set_title('Per-category frozen matches; human review pending')
    fig.text(.5,-.03,'Frozen ID gaps omit existing v6 resource/logic evidence. Bars do not establish unique tool capability.',ha='center',fontsize=8)
    ax.legend(fontsize=7,ncol=3);save(fig,'figure_4_categories')
    capabilities=[r for r in rows('table_II_capabilities.csv') if r['configuration']!='combined_optional'];fig,ax=plt.subplots(figsize=(9,4))
    statuses=sorted({s for row in capabilities for s in json.loads(row['statuses'])});bottom=[0]*len(capabilities)
    for status in statuses:
        heights=[json.loads(row['statuses']).get(status,0) for row in capabilities]
        ax.bar(range(len(capabilities)),heights,bottom=bottom,label=status);bottom=[a+b for a,b in zip(bottom,heights)]
    ax.set_xticks(range(len(capabilities)),[r['configuration'] for r in capabilities],rotation=20,ha='right')
    ax.set_ylabel('Cases');ax.set_title('Operational completion; no function/path coverage certification');ax.legend(fontsize=8)
    save(fig,'figure_5_eligibility')


if __name__=='__main__':main()
