import {useEffect,useState} from 'react'

export const EXPLORER_SESSION_KEY='smartparse.explorer.v1'
function initialLayout() {
  const fallback={collapsed:false,mobileOpen:false,width:224}
  try {
    const saved=JSON.parse(sessionStorage.getItem(EXPLORER_SESSION_KEY)||'null')
    if(!saved||typeof saved!=='object')return fallback
    return {collapsed:saved.collapsed===true,mobileOpen:saved.mobileOpen===true,
      width:typeof saved.width==='number'&&Number.isFinite(saved.width)?Math.max(180,Math.min(360,saved.width)):224}
  }catch{return fallback}
}

export function useExplorer() {
  const [layout,setLayout]=useState(initialLayout)
  const [viewport,setViewport]=useState(()=>window.innerWidth)
  const narrow=viewport<=900
  useEffect(()=>{
    const resized=()=>setViewport(window.innerWidth)
    window.addEventListener('resize',resized);return()=>window.removeEventListener('resize',resized)
  },[])
  useEffect(()=>{try{sessionStorage.setItem(EXPLORER_SESSION_KEY,JSON.stringify(layout))}catch{/* In-memory preference still works if storage is blocked. */}},[layout])
  const maxWidth=narrow?Math.min(360,Math.max(180,viewport-60)):360
  return {
    visible:narrow?layout.mobileOpen:!layout.collapsed,width:Math.min(layout.width,maxWidth),maxWidth,
    toggle:()=>setLayout(current=>narrow?{...current,mobileOpen:!current.mobileOpen}:{...current,collapsed:!current.collapsed}),
    dismissMobile:()=>{if(narrow)setLayout(current=>({...current,mobileOpen:false}))},
    resize:(width:number)=>setLayout(current=>({...current,width:Math.max(180,Math.min(maxWidth,width))})),
  }
}
