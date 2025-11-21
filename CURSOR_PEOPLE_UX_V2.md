# People UX v2 - Make It a Real Mini-CRM

## Current State vs. Desired State

### ✅ What Already Works
- Contacts have Edit button (Pencil icon)
- Contacts have "Add to Group" button (Users icon)  
- Contacts have Delete button
- Groups tab exists with "New Group" button
- Groups can be created with name + description

### ❌ What's Missing (Design Smell)
- **Groups have NO actions** - just a table with no "View/Manage"
- **Can't see group members** - no detail view
- **Can't add members to a group** from the group side
- **Can't remove members from a group** 
- Groups feel like read-only metadata, not first-class entities

---

## Step 1: Add Group Management Actions

### Target File
`apps/web/app/app/people/page.tsx`

### What to Change

#### 1.1 - Add State for Group Detail Dialog

Find this section (around line 80-95):
```typescript
const [groupDialogOpen, setGroupDialogOpen] = useState(false)
const [groupForm, setGroupForm] = useState({ name: "", description: "" })
```

**ADD** right after:
```typescript
const [viewGroupDialogOpen, setViewGroupDialogOpen] = useState(false)
const [selectedGroup, setSelectedGroup] = useState<ContactGroup | null>(null)
const [groupMembers, setGroupMembers] = useState<Array<{
  id: string
  name: string
  email: string
  type: string
  member_type: "contact" | "sponsored_agent"
}>>([])
const [loadingGroupMembers, setLoadingGroupMembers] = useState(false)
const [addMembersToGroupDialogOpen, setAddMembersToGroupDialogOpen] = useState(false)
const [selectedMemberIdsForGroup, setSelectedMemberIdsForGroup] = useState<string[]>([])
```

#### 1.2 - Add Function to Load Group Members

Find the `loadGroups()` function (around line 155). **ADD** right after:

```typescript
async function loadGroupMembers(groupId: string) {
  setLoadingGroupMembers(true)
  try {
    const res = await fetch(`/api/proxy/v1/contact-groups/${groupId}`, { cache: "no-store" })
    if (res.ok) {
      const data = await res.json()
      setGroupMembers(data.members || [])
    }
  } catch (error) {
    console.error("Failed to load group members:", error)
    toast({
      title: "Error",
      description: "Failed to load group members",
      variant: "destructive",
    })
  } finally {
    setLoadingGroupMembers(false)
  }
}

async function handleAddMembersToGroup() {
  if (!selectedGroup || selectedMemberIdsForGroup.length === 0) return

  try {
    // Build members array from selected IDs
    const members = selectedMemberIdsForGroup.map((id) => {
      // Check if it's a contact or sponsored agent
      const contact = contacts.find((c) => c.id === id)
      if (contact) {
        return { member_type: "contact" as const, member_id: id }
      }
      const agent = sponsoredAccounts.find((s) => s.account_id === id)
      if (agent) {
        return { member_type: "sponsored_agent" as const, member_id: id }
      }
      return null
    }).filter(Boolean)

    const res = await fetch(`/api/proxy/v1/contact-groups/${selectedGroup.id}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ members }),
    })

    if (!res.ok) {
      throw new Error("Failed to add members")
    }

    toast({
      title: "Success",
      description: `Added ${members.length} member(s) to ${selectedGroup.name}`,
    })

    // Reload group members
    await loadGroupMembers(selectedGroup.id)
    await loadGroups()
    setAddMembersToGroupDialogOpen(false)
    setSelectedMemberIdsForGroup([])
  } catch (error) {
    console.error("Failed to add members:", error)
    toast({
      title: "Error",
      description: "Failed to add members to group",
      variant: "destructive",
    })
  }
}

async function handleRemoveMemberFromGroup(memberId: string, memberType: "contact" | "sponsored_agent") {
  if (!selectedGroup) return

  try {
    const res = await fetch(`/api/proxy/v1/contact-groups/${selectedGroup.id}/members`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_type: memberType, member_id: memberId }),
    })

    if (!res.ok) {
      throw new Error("Failed to remove member")
    }

    toast({
      title: "Success",
      description: "Member removed from group",
    })

    // Reload group members
    await loadGroupMembers(selectedGroup.id)
    await loadGroups()
  } catch (error) {
    console.error("Failed to remove member:", error)
    toast({
      title: "Error",
      description: "Failed to remove member from group",
      variant: "destructive",
    })
  }
}
```

#### 1.3 - Add Actions Column to Groups Table

Find the Groups table (around line 1019-1040). **REPLACE**:

```typescript
<TableHeader>
  <TableRow>
    <TableHead>Name</TableHead>
    <TableHead>Description</TableHead>
    <TableHead>Members</TableHead>
  </TableRow>
</TableHeader>
```

**WITH**:

```typescript
<TableHeader>
  <TableRow>
    <TableHead>Name</TableHead>
    <TableHead>Description</TableHead>
    <TableHead>Members</TableHead>
    <TableHead className="text-right">Actions</TableHead>
  </TableRow>
</TableHeader>
```

And **REPLACE** the TableBody:

```typescript
<TableBody>
  {groups.map((group) => (
    <TableRow key={group.id}>
      <TableCell className="font-medium">{group.name}</TableCell>
      <TableCell>{group.description || "—"}</TableCell>
      <TableCell>{group.member_count ?? 0}</TableCell>
    </TableRow>
  ))}
</TableBody>
```

**WITH**:

```typescript
<TableBody>
  {groups.map((group) => (
    <TableRow key={group.id}>
      <TableCell className="font-medium">{group.name}</TableCell>
      <TableCell>{group.description || "—"}</TableCell>
      <TableCell>{group.member_count ?? 0}</TableCell>
      <TableCell className="text-right space-x-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={async () => {
            setSelectedGroup(group)
            await loadGroupMembers(group.id)
            setViewGroupDialogOpen(true)
          }}
        >
          <Users className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleDeleteGroup(group.id, group.name)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </TableCell>
    </TableRow>
  ))}
</TableBody>
```

#### 1.4 - Add Group Detail Dialog

Find the end of the component, **BEFORE** the closing `</div>` (around line 1041). **ADD**:

```typescript
      {/* View/Manage Group Dialog */}
      <Dialog open={viewGroupDialogOpen} onOpenChange={setViewGroupDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Manage Group: {selectedGroup?.name}</DialogTitle>
            <DialogDescription>
              {selectedGroup?.description || "No description"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Members ({groupMembers.length})</h4>
              <Button
                size="sm"
                onClick={() => {
                  setAddMembersToGroupDialogOpen(true)
                }}
              >
                <UserPlus className="h-4 w-4 mr-2" />
                Add Members
              </Button>
            </div>
            
            {loadingGroupMembers ? (
              <div className="text-center py-8 text-muted-foreground">Loading members...</div>
            ) : groupMembers.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No members yet. Click "Add Members" to add people to this group.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {groupMembers.map((member) => (
                    <TableRow key={`${member.member_type}-${member.id}`}>
                      <TableCell className="font-medium">{member.name}</TableCell>
                      <TableCell>{member.email || "—"}</TableCell>
                      <TableCell>
                        <Badge variant={member.member_type === "sponsored_agent" ? "default" : "outline"}>
                          {member.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveMemberFromGroup(member.id, member.member_type)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewGroupDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Members to Group Dialog */}
      <Dialog open={addMembersToGroupDialogOpen} onOpenChange={setAddMembersToGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Members to {selectedGroup?.name}</DialogTitle>
            <DialogDescription>
              Select contacts or sponsored agents to add to this group
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2 max-h-96 overflow-y-auto">
              <h4 className="text-sm font-semibold mb-2">Available People</h4>
              {people.map((person) => {
                // Check if already in group
                const isInGroup = groupMembers.some((m) => m.id === person.id)
                const isSelected = selectedMemberIdsForGroup.includes(person.id)
                
                return (
                  <div
                    key={person.id}
                    className={`flex items-center space-x-2 p-2 rounded border ${
                      isInGroup ? "opacity-50 bg-muted" : "cursor-pointer hover:bg-accent"
                    }`}
                    onClick={() => {
                      if (isInGroup) return
                      setSelectedMemberIdsForGroup((prev) =>
                        isSelected
                          ? prev.filter((id) => id !== person.id)
                          : [...prev, person.id]
                      )
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      disabled={isInGroup}
                      onChange={() => {}}
                      className="h-4 w-4"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{person.name}</p>
                      <p className="text-xs text-muted-foreground">{person.email || person.displayType}</p>
                    </div>
                    {isInGroup && (
                      <Badge variant="outline" className="text-xs">
                        Already in group
                      </Badge>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setAddMembersToGroupDialogOpen(false)
                setSelectedMemberIdsForGroup([])
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddMembersToGroup}
              disabled={selectedMemberIdsForGroup.length === 0}
            >
              Add {selectedMemberIdsForGroup.length} Member(s)
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
```

#### 1.5 - Add Missing Delete Group Handler

Find where other delete handlers are (around the contact delete handler). **ADD**:

```typescript
async function handleDeleteGroup(groupId: string, groupName: string) {
  if (!confirm(`Delete group "${groupName}"? Members will not be deleted, just the group.`)) {
    return
  }

  try {
    const res = await fetch(`/api/proxy/v1/contact-groups/${groupId}`, {
      method: "DELETE",
    })

    if (!res.ok) {
      throw new Error("Failed to delete group")
    }

    toast({
      title: "Success",
      description: `Group "${groupName}" deleted`,
    })

    await loadGroups()
  } catch (error) {
    console.error("Failed to delete group:", error)
    toast({
      title: "Error",
      description: "Failed to delete group",
      variant: "destructive",
    })
  }
}
```

---

## Step 2: Verify Backend DELETE Endpoint for Groups

### Target File
`apps/api/src/api/routes/contact_groups.py`

### Check if DELETE endpoint exists

Look for:
```python
@router.delete("/contact-groups/{group_id}")
def delete_contact_group(...):
    ...
```

**If it DOESN'T exist**, add:

```python
@router.delete("/contact-groups/{group_id}")
def delete_contact_group(
    group_id: str,
    request: Request,
    account_id: str = Depends(require_account_id),
):
    """
    Delete a contact group.
    
    This only deletes the group itself, not the contacts/agents in it.
    """
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Verify ownership
        cur.execute("""
            SELECT 1 FROM contact_groups
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (group_id, account_id))
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Delete group (members will cascade due to FK)
        cur.execute("""
            DELETE FROM contact_groups
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (group_id, account_id))
        
        conn.commit()
    
    return {"ok": True, "message": "Group deleted"}
```

---

## Step 3: Add Frontend Proxy Route for DELETE

### Target File
`apps/web/app/api/proxy/v1/contact-groups/[groupId]/route.ts`

### Check if DELETE handler exists

Look for:
```typescript
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ groupId: string }> }) {
  ...
}
```

**If it DOESN'T exist**, add:

```typescript
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ groupId: string }> }) {
  const cookieHeader = req.headers.get("cookie") || ""
  const { groupId } = await params

  const res = await fetch(`${API_BASE}/v1/contact-groups/${groupId}`, {
    method: "DELETE",
    headers: {
      cookie: cookieHeader,
    },
    cache: "no-store",
  })

  const text = await res.text()
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  })
}
```

---

## Expected Behavior After Changes

### Groups Tab - Before
```
┌────────────────────────────────────────────┐
│ Name        │ Description │ Members        │
├────────────────────────────────────────────┤
│ VIP Clients │ High-value  │ 2             │
└────────────────────────────────────────────┘
```
❌ No way to see who the 2 members are  
❌ No way to add more members  
❌ No way to remove members  

### Groups Tab - After
```
┌──────────────────────────────────────────────────────────┐
│ Name        │ Description │ Members │ Actions           │
├──────────────────────────────────────────────────────────┤
│ VIP Clients │ High-value  │ 2       │ [👁️ View] [🗑️]  │
└──────────────────────────────────────────────────────────┘
```
✅ Click "View" → See detailed member list  
✅ "Add Members" button → Multi-select from all people  
✅ "Remove" on each member  
✅ Delete group itself  

### Group Detail Dialog
```
┌─────────────────────────────────────────────────┐
│ Manage Group: VIP Clients                       │
│ High-value clients for monthly reports          │
│                                                  │
│ Members (2)                [+ Add Members]      │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ Name         │ Email       │ Type   │ Remove││
│ ├─────────────────────────────────────────────┤ │
│ │ Alice        │ alice@...   │ Client │ [🗑️]  ││
│ │ Bob          │ bob@...     │ Client │ [🗑️]  ││
│ └─────────────────────────────────────────────┘ │
│                                                  │
│                                    [Close]      │
└─────────────────────────────────────────────────┘
```

---

## Testing Checklist

- [ ] Create empty group (just name + description)
- [ ] Group appears in list with 0 members
- [ ] Click "View" on group
- [ ] See empty state message
- [ ] Click "Add Members"
- [ ] Select 2-3 people (mix of contacts and sponsored agents if affiliate)
- [ ] Click "Add X Member(s)"
- [ ] Members appear in group detail view
- [ ] Group list shows updated member count
- [ ] Click "Remove" on a member
- [ ] Member removed, count updates
- [ ] Delete entire group
- [ ] Members still exist in People tab (not deleted)

---

## Files to Modify

1. `apps/web/app/app/people/page.tsx` - Add group management UI
2. `apps/api/src/api/routes/contact_groups.py` - Add DELETE endpoint (if missing)
3. `apps/web/app/api/proxy/v1/contact-groups/[groupId]/route.ts` - Add DELETE proxy

---

## Outcome

After these changes:
- ✅ Groups are **first-class** - can create, view, edit membership, delete
- ✅ Contacts remain **first-class** - can edit, add to groups, manage groups
- ✅ Schedules become **pure consumers** - just pick existing groups
- ✅ Affiliate has a real **mini-CRM** for managing their network

This matches your mental model exactly: **People is the brain, Schedules is the delivery engine**.

