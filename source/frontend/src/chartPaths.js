/**
 * Shape-preserving cubic Hermite path through observed points.
 * The curve is a display treatment only. It never changes or creates a
 * telemetry observation, and flat/turning intervals do not overshoot.
 */
export function smoothChartPath(points) {
  if (!Array.isArray(points) || !points.length) return '';
  const valid = points.every((p,i)=>Number.isFinite(p?.x)&&Number.isFinite(p?.y)&&
    (i===0||p.x>points[i-1].x));
  if(!valid)return '';
  const f=n=>Number(n).toFixed(2);
  if(points.length===1)return 'M'+f(points[0].x)+' '+f(points[0].y);
  const delta = [];
  for(let i=0;i<points.length-1;i++){
    delta.push((points[i+1].y-points[i].y)/(points[i+1].x-points[i].x));
  }
  const tangent = points.map((_,i)=>{
    if(i===0)return delta[0];
    if(i===points.length-1)return delta.at(-1);
    const left=delta[i-1],right=delta[i];
    if(left===0||right===0||left*right<=0)return 0;
    const h0=points[i].x-points[i-1].x,h1=points[i+1].x-points[i].x;
    const w1=2*h1+h0,w2=h1+2*h0;
    return (w1+w2)/(w1/left+w2/right);
  });
  let path='M'+f(points[0].x)+' '+f(points[0].y);
  for(let i=0;i<points.length-1;i++){
    const a=points[i],b=points[i+1],dx=b.x-a.x,slope=delta[i];
    let m0=tangent[i],m1=tangent[i+1];
    if(slope===0){m0=0;m1=0;}
    else{
      const alpha=m0/slope,beta=m1/slope;
      const radius=Math.hypot(alpha,beta);
      if(radius>3){const s=3/radius;m0=s*alpha*slope;m1=s*beta*slope;}
    }
    path+=' C'+f(a.x+dx/3)+' '+f(a.y+m0*dx/3)+
      ' '+f(b.x-dx/3)+' '+f(b.y-m1*dx/3)+
      ' '+f(b.x)+' '+f(b.y);
  }
  return path;
}
