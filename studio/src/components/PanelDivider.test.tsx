import {fireEvent, render, screen} from '@testing-library/react'
import {expect, test, vi} from 'vitest'
import {PanelDivider} from './PanelDivider'

test('keyboard resizing clamps horizontal width and supports Home / End',()=>{
  const change=vi.fn()
  render(<PanelDivider axis="vertical" label="Size" value={72} min={34} max={72} step={2} onChange={change} onDrag={vi.fn()}/> )
  const divider=screen.getByRole('separator')
  fireEvent.keyDown(divider,{key:'ArrowRight'});expect(change).toHaveBeenLastCalledWith(72)
  fireEvent.keyDown(divider,{key:'ArrowLeft'});expect(change).toHaveBeenLastCalledWith(70)
  fireEvent.keyDown(divider,{key:'Home'});expect(change).toHaveBeenLastCalledWith(34)
  fireEvent.keyDown(divider,{key:'End'});expect(change).toHaveBeenLastCalledWith(72)
})
test('Up expands bottom details, Down reduces it',()=>{
  const change=vi.fn()
  render(<PanelDivider axis="horizontal" label="Height" value={144} min={120} max={420} step={20} onChange={change} onDrag={vi.fn()}/> )
  fireEvent.keyDown(screen.getByRole('separator'),{key:'ArrowUp'});expect(change).toHaveBeenLastCalledWith(164)
  fireEvent.keyDown(screen.getByRole('separator'),{key:'ArrowDown'});expect(change).toHaveBeenLastCalledWith(124)
})
test('pointer cancellation and unmount remove drag listeners',()=>{
  const drag=vi.fn()
  const {unmount}=render(<PanelDivider axis="vertical" label="Size" value={58} min={34} max={72} step={2} onChange={vi.fn()} onDrag={drag}/> )
  fireEvent.pointerDown(screen.getByRole('separator'),{button:0,pointerId:1})
  fireEvent.pointerMove(window,{pointerId:1,clientX:100});expect(drag).toHaveBeenCalledTimes(1)
  fireEvent.pointerCancel(window,{pointerId:1})
  fireEvent.pointerMove(window,{pointerId:1,clientX:200});expect(drag).toHaveBeenCalledTimes(1)
  fireEvent.pointerDown(screen.getByRole('separator'),{button:0,pointerId:2});unmount()
  expect(document.body).not.toHaveClass('resizing-panels')
  fireEvent.pointerMove(window,{pointerId:2});expect(drag).toHaveBeenCalledTimes(1)
})
