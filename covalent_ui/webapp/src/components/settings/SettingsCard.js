/**
 * Copyright 2021 Agnostiq Inc.
 *
 * This file is part of Covalent.
 *
 * Licensed under the GNU Affero General Public License 3.0 (the "License").
 * A copy of the License may be obtained with this software package or at
 *
 *      https://www.gnu.org/licenses/agpl-3.0.en.html
 *
 * Use of this file is prohibited except in compliance with the License. Any
 * modifications or derivative works of this file must retain this copyright
 * notice, and modified files must contain a notice indicating that they have
 * been altered from the originals.
 *
 * Covalent is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
 *
 * Relief from the License may be granted by purchasing a commercial license.
 */

import React, { useEffect, useState } from 'react';
import {
  Container, Grid, Box, Input, InputLabel, Radio, RadioGroup, Button,
  Stack, Snackbar, SvgIcon, InputAdornment, IconButton
} from '@mui/material';
import { Clear as ClearIcon, Search as SearchIcon } from '@mui/icons-material'
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Collapse from '@mui/material/Collapse';
import ExpandMore from '@mui/icons-material/ExpandMore';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import { settingsResults, updateSettings } from '../../redux/settingsSlice';
import { useDispatch, useSelector } from 'react-redux';
import _, { capitalize } from 'lodash'
import Skeleton from '@mui/material/Skeleton';
import { ReactComponent as closeIcon } from '../../assets/close.svg'
import { toggleLatticeDrawer } from '../../redux/popupSlice'

const SettingsCard = () => {
  const dispatch = useDispatch()
  const [open, setOpen] = useState(false)
  const [subMenu, setSubMenu] = useState([])
  const [resultKey, setResultKey] = useState("sdk")
  const [resultOutput, setResultOutput] = useState()
  const settings_result = useSelector((state) => state.settingsResults.settingsList)
  const callSocketApi = useSelector((state) => state.common.callSocketApi)
  const [openSnackbar, setOpenSnackbar] = useState(false)
  const [snackbarMessage, setSnackbarMessage] = useState(null)
  const [isDisabled, setIsDisabled] = useState(false)
  const [handle, setHandle] = useState('')
  const [searchData, setSearchData] = useState(settings_result)
  const [searchKey, setSearchKey] = useState('')
  const [restoreData, setRestoreData] = useState()
  const [valueChange, setValueChange] = useState(false)
  const [serverName, setServerName] = useState('server')
  const [accName, setAccName] = useState('client')
  const menuCallResult = useSelector((state) => state.dataRes.popupData)
  const [clientDetail, setClientDetail] = useState(null)
  const [serverDetail, setServerDetail] = useState(null)

  useEffect(() => {
    dispatch(settingsResults())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callSocketApi])

  useEffect(() => {
    if (valueChange) {
      const settingObj = {
        isChanged: valueChange,
        data: resultOutput,
        nodeName: resultKey,
        mainKey: accName
      }
      dispatch(toggleLatticeDrawer(settingObj))
    }
    else {
      const settingObj = {
        isChanged: valueChange
      }
      dispatch(toggleLatticeDrawer(settingObj))
    }
  }, [valueChange, resultOutput])

  useEffect(() => {
    if (settings_result) {
      setSearchData(Object.values(settings_result)[0])
      setClientDetail(Object.values(settings_result)[0])
      setServerDetail(Object.values(settings_result)[1])
    }
  }, [settings_result])

  useEffect(() => {
    if (_.size(searchData) !== 0) {
      setResultOutput(Object.values(searchData)[0])
      setRestoreData(Object.values(searchData)[0])
    }
  }, [searchData])

  const handleSubmit = (event) => {
    event.preventDefault();
    const updateData = {
      [accName]: {
        [resultKey]: resultOutput
      }
    }
    dispatch(updateSettings(updateData)).then((action) => {
      if (action.type === updateSettings.fulfilled.type) {
        setOpenSnackbar(true)
        setSnackbarMessage('Settings Updated Successfully')
        setValueChange(false)
        setClientDetail(currValue => ({
          ...currValue,
          [resultKey]: resultOutput
        }))
      } else if (action.type === updateSettings.rejected.type) {
        setOpenSnackbar(true)
        setSnackbarMessage('Something went wrong and could not settings updated!')
      }
    })
    setHandle('')
  };

  const getSubmenuName = (name) => {
    let formattedName = name;
    const uSpliit = name.includes("_");
    if (uSpliit) {
      var a = name.replace(name.at(0), name.at(0).toLocaleUpperCase()).substring(0, name.indexOf("_"))
      var b = name.replace(name.at(0), name.at(0).toLocaleUpperCase()).substring(name.indexOf("_") + 1, name.length)
      formattedName = a + " " + b.replace(b.at(0), b.at(0).toLocaleUpperCase())
    }
    else {
      if (name === 'slurm') {
        formattedName = name.toUpperCase();
      }
      else if (name === 'dask') {
        formattedName = name.toUpperCase();
      }
      else {
        formattedName = name.charAt(0).toUpperCase() + name.slice(1);
      }
    }
    return formattedName
  }

  const getLabelName = (name) => {
    let formattedName = name;
    const uSpliit = name.includes("_");
    if (uSpliit) {
      var a = name.replace(name.at(0), name.at(0).toLocaleUpperCase()).substring(0, name.indexOf("_"))
      var b = name.replace(name.at(0), name.at(0).toLocaleUpperCase()).substring(name.indexOf("_") + 1, name.length)
      formattedName = a + " " + b.replace(b.at(0), b.at(0))
    }
    else {
      if (name === 'sdk') {
        formattedName = name.toUpperCase();
      }
      else {
        formattedName = name.charAt(0).toUpperCase() + name.slice(1);
      }
    }
    if (formattedName === 'Cache dir') {
      formattedName = 'Cache directory'
    }
    else if (formattedName === 'Results dir') {
      formattedName = 'Results directory'
    }
    else if (formattedName === 'Executor dir') {
      formattedName = 'Executor directory'
    }
    else if (formattedName === 'Log stdout') {
      formattedName = 'Log standard out'
    }
    else if (formattedName === 'Log dir') {
      formattedName = 'Log directory'
    }
    else if (formattedName === 'Base dir') {
      formattedName = 'Base directory'
    }
    return formattedName
  }

  const getSettingsName = (name) => {
    let formattedName = name;
    const uSpliit = name.includes("_");
    if (uSpliit) {
      var a = name.replace(name.at(0), name.at(0).toLocaleUpperCase()).substring(0, name.indexOf("_"))
      var b = name.replace(name.at(0), name.at(0).toLocaleUpperCase()).substring(name.indexOf("_") + 1, name.length)
      formattedName = a + " " + b.replace(b.at(0), b.at(0).toLocaleUpperCase())
    }
    else {
      if (name === 'sdk' || name === "dask") {
        formattedName = name.toUpperCase();
      }
      else {
        formattedName = name.charAt(0).toUpperCase() + name.slice(1);
      }
    }
    return formattedName
  }

  const isChildHasList = (item) => {
    let childIsObject = false;
    _.map(item, function (value) {
      if (_.isObject(value)) childIsObject = true;
    })
    return childIsObject;
  }

  const handleClick = (item) => {
    let tmpList = [];
    _.map(item, function (value, key) {
      if (_.isObject(value)) {
        setOpen(!open);
        tmpList.push(key)
      }
      else {
        setOpen(false);
      }
    })
    setSubMenu(tmpList);
  };

  const menuClick = (value, key, panel) => {
    if (panel === "client") {
      setIsDisabled(false)
    }
    else {
      setIsDisabled(true)
    }
    setRestoreData(value)
    if (menuCallResult.isChanged) {
      const updateData = {
        [accName]: {
          [resultKey]: resultOutput
        }
      }
      dispatch(updateSettings(updateData)).then((action) => {
        if (action.type === updateSettings.fulfilled.type) {
          setOpenSnackbar(true)
          setSnackbarMessage('Settings Updated Successfully')
          setValueChange(false)
          setClientDetail(currValue => ({
            ...currValue,
            [resultKey]: resultOutput
          }))
        } else if (action.type === updateSettings.rejected.type) {
          setOpenSnackbar(true)
          setSnackbarMessage('Something went wrong and could not settings updated!')
        }
      })
      setHandle('')
      setIsDisabled(false)
    }
    else {
      setValueChange(false)
      setResultKey(key)
      setResultOutput(value)
    }
  }

  const handleKeypress = (event) => {
    setHandle(event.key)
    setValueChange(true)
  }

  const onInputExecutorChange = (e, subkey, key) => {
    setResultOutput(currValue => ({
      ...currValue,
      [key]: {
        ...currValue[key],
        [subkey]: e.target.value
      },
    }))
  }

  const handleChange = (e, key) => {
    setHandle(e.target.value)
    setValueChange(true)
    setResultOutput(currValue => ({
      ...currValue,
      [key]: e.target.value
    }))
  }

  const cancelButton = () => {
    if (handle) {
      setResultOutput(restoreData)
      setHandle('')
      setValueChange(false)
    }
  }

  const handleInputChange = (e) => {
    setSearchKey(e.target.value)
    const filterData = Object.fromEntries(Object.entries(clientDetail).filter(([key]) =>
      key.includes(e.target.value)))
    const filterData1 = Object.fromEntries(Object.entries(serverDetail).filter(([key]) =>
      key.includes(e.target.value)))
    setClientDetail(filterData)
    setServerDetail(filterData1)
  };

  const handleSearchClear = () => {
    setSearchKey('')
    setClientDetail(Object.values(settings_result)[0])
    setServerDetail(Object.values(settings_result)[1])
  }

  const handleSubmenuClick = (menu) => {
    document.getElementById(menu).scrollIntoView({ behavior: "smooth" });
  }

  const onInputChange = (e, key) => {
    setResultOutput(currValue => ({
      ...currValue,
      [key]: e.target.value
    }))
  }

  return (
    <Container maxWidth="xl" sx={{ mb: 4, mt: 7.5, ml: 4 }}>
      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        message={snackbarMessage}
        onClose={() => setOpenSnackbar(false)}
        action={
          <SvgIcon
            sx={{
              mt: 2,
              zIndex: 2,
              cursor: 'pointer',
            }}
            component={closeIcon}
            onClick={() => setOpenSnackbar(false)}
          />
        }
      />
      <Typography variant="h4" component="h4" sx={{ mb: 5 }}>
        Settings
      </Typography>
      {_.size(settings_result) !== 0 ?

        <Box>
          <Grid container spacing={3}>
            <Grid item xs={3}
              sx={(theme) => ({
                borderRight: 1,
                borderColor: theme.palette.background.coveBlack02,
              })}
            >
              <Box>
                <Input sx={{
                  px: 2,
                  py: 0.5,
                  width: "95%",
                  height: '40px',
                  border: '1px solid #303067',
                  borderRadius: '60px',
                  mb: 3
                }}
                  disableUnderline
                  value={searchKey}
                  startAdornment={
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: 'text.secondary', fontSize: 18 }} />
                    </InputAdornment>
                  }
                  endAdornment={
                    <InputAdornment
                      position="end"
                      sx={{ visibility: searchKey !== '' ? 'visible' : 'hidden' }}
                    >
                      <IconButton size="small" onClick={() => handleSearchClear()}>
                        <ClearIcon fontSize="inherit" sx={{ color: 'text.secondary' }} />
                      </IconButton>
                    </InputAdornment>
                  }
                  onChange={(e) => handleInputChange(e)}
                  placeholder="Search" />
                <Typography variant="h6" component="h6"
                  sx={(theme) => ({ color: theme.palette.primary.light, fontWeight: 'bold', mb: 2 })}>
                  {capitalize(accName)}
                </Typography>
                {_.map(clientDetail, function (menuValue, menuKey) {
                  return (
                    <ListItem disablePadding>
                      <ListItemButton
                        onClick={isChildHasList ? () => handleClick(menuValue) : () => { }}
                        sx={{ right: isChildHasList(menuValue) ? '0px' : '0px' }}>
                        {isChildHasList(menuValue) &&
                          <ListItemIcon>
                            {open ? <ExpandMore /> : <KeyboardArrowRightIcon />}
                          </ListItemIcon>
                        }
                        <ListItemText inset primary={getSettingsName(menuKey)}
                          onClick={() => menuClick(menuValue, menuKey, accName)}
                          disableTypography
                          sx={{
                            color: resultKey === menuKey ? 'white' : 'text.primary',
                            pl: "0px", fontSize: '18px', fontWeight: resultKey === menuKey ?
                              'bold' : 'normal'
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  )
                })
                }

                {open &&
                  <Collapse in={open} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding>
                      {
                        _.map(subMenu, function (value, key) {
                          return (
                            <ListItem disablePadding>
                              <ListItemButton sx={{ pl: 9, pt: 0.3, pb: 0.3 }}>
                                <ListItemText inset primary={getSubmenuName(value)}
                                  onClick={() => handleSubmenuClick(value)}
                                  disableTypography
                                  sx={{ pl: "0px", fontSize: '18px' }} />
                              </ListItemButton>
                            </ListItem>
                          )
                        })
                      }
                    </List>
                  </Collapse>
                }
              </Box>

              <Box>
                <Typography variant="h6" component="h6"
                  sx={(theme) => ({ color: theme.palette.primary.light, fontWeight: 'bold', mb: 2, mt: 2 })}>
                  {capitalize(serverName)}
                </Typography>
                {_.map(serverDetail, function (menuValue, menuKey) {
                  return (
                    <ListItem disablePadding>
                      <ListItemButton
                        onClick={isChildHasList ? () => handleClick(menuValue) : () => { }}
                        sx={{ right: isChildHasList(menuValue) ? '0px' : '0px' }}>
                        {isChildHasList(menuValue) &&
                          <ListItemIcon>
                            {open ? <ExpandMore /> : <KeyboardArrowRightIcon />}
                          </ListItemIcon>
                        }
                        <ListItemText inset primary={getSettingsName(menuKey)}
                          onClick={() => menuClick(menuValue, menuKey)}
                          disableTypography
                          sx={{
                            color: resultKey === menuKey ? 'white' : 'text.primary',
                            pl: "0px", fontSize: '18px', fontWeight: resultKey === menuKey ?
                              'bold' : 'normal'
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  )
                })
                }
              </Box>

            </Grid>
            <Grid item xs={9}>
              <Typography variant="h6" component="h6" sx={{ fontWeight: 'bold' }}>
                {getSettingsName(resultKey)}
              </Typography>
              <Grid container spacing={3} sx={{ mt: 2 }}>
                <Grid item xs={7}>
                  <form onSubmit={handleSubmit} id="get__pop_id">
                    {
                      _.map(resultOutput, function (value, key) {
                        return (
                          <Box sx={{ mb: 3 }}>
                            {
                              _.isObject(value)
                                ?
                                <Box id={key}>
                                  <Typography variant="h6" component="h6"
                                    sx={(theme) => ({ color: theme.palette.primary.light, fontWeight: 'bold' })}>
                                    {getSettingsName(key)}
                                  </Typography>
                                  {
                                    _.map(value, function (item, key1) {
                                      return (
                                        <Box sx={{ mt: 3 }}>
                                          {value === "true" || value === "false" ?
                                            <FormControl>
                                              <FormLabel id="demo-row-radio-buttons-group-label"
                                                sx={(theme) => ({
                                                  fontSize: '16px',
                                                  color: 'text.primary'
                                                })}> {getSettingsName(key1)}</FormLabel>
                                              <RadioGroup
                                                row
                                                onChange={handleChange}
                                                aria-labelledby="demo-row-radio-buttons-group-label"
                                                name="row-radio-buttons-group"
                                              >
                                                <FormControlLabel value="true"
                                                  disabled={isDisabled} control={<Radio />} label="True" />
                                                <FormControlLabel value="false"
                                                  disabled={isDisabled} control={<Radio />} label="False" />
                                              </RadioGroup>
                                            </FormControl>
                                            :
                                            <>
                                              <InputLabel variant="standard" htmlFor="uncontrolled-native"
                                                sx={{
                                                  fontSize: '16px',
                                                  mb: 1,
                                                  color: 'text.primary'
                                                }}>
                                                {getLabelName(key1)}
                                              </InputLabel>
                                              <Input sx={{
                                                px: 2,
                                                py: 0.5,
                                                width: "100%",
                                                height: '45px',
                                                border: '1px solid #303067',
                                                borderRadius: '60px',
                                              }}
                                                disabled={isDisabled}
                                                onKeyDown={handleKeypress}
                                                name={key1}
                                                onChange={(e) => onInputExecutorChange(e, key1, key)}
                                                value={item}
                                                disableUnderline
                                                placeholder={key1} />
                                            </>
                                          }
                                        </Box>
                                      )
                                    })
                                  }
                                </Box>
                                :
                                <>
                                  {value === "true" || value === "false" ?
                                    <FormControl>
                                      <FormLabel id="demo-row-radio-buttons-group-label"
                                        sx={(theme) => ({
                                          fontSize: '16px',
                                          color: 'text.primary'
                                        })}> {getSettingsName(key)}</FormLabel>
                                      <RadioGroup
                                        row
                                        aria-labelledby="demo-row-radio-buttons-group-label"
                                        name={key}
                                        value={value}
                                        onChange={(e) => handleChange(e, key)}
                                      >
                                        <FormControlLabel disabled={isDisabled} value="true"
                                          control={<Radio />} label="True" />
                                        <FormControlLabel disabled={isDisabled}
                                          value="false" control={<Radio />} label="False" />
                                      </RadioGroup>
                                    </FormControl>
                                    :
                                    <>
                                      <InputLabel variant="standard" htmlFor="uncontrolled-native"
                                        sx={{
                                          fontSize: '16px',
                                          mb: 1,
                                          color: 'text.primary'
                                        }}>
                                        {getLabelName(key)}
                                      </InputLabel>
                                      <Input sx={{
                                        px: 2,
                                        py: 0.5,
                                        width: "100%",
                                        height: '45px',
                                        border: '1px solid #303067',
                                        borderRadius: '60px',
                                      }}
                                        disabled={isDisabled}
                                        onKeyDown={handleKeypress}
                                        name={key}
                                        onChange={(e) => onInputChange(e, key)}
                                        value={value}
                                        disableUnderline
                                        placeholder={key} />
                                    </>
                                  }
                                </>
                            }
                          </Box>
                        )
                      })
                    }

                    {!isDisabled &&
                      <Stack spacing={2} direction="row" sx={{ float: 'right' }}>
                        <Button variant="outlined"
                          onClick={() => cancelButton()}
                          sx={(theme) => ({
                            padding: '8px 20px',
                            border: '1px solid #6473FF',
                            borderRadius: '60px',
                            color: 'white',
                            fontSize: '16px',
                            textTransform: 'capitalize'
                          })}>Cancel</Button>
                        <Button var
                          type="submit"
                          sx={(theme) => ({
                            background: '#5552FF',
                            borderRadius: '60px',
                            color: 'white',
                            padding: '8px 30px',
                            fontSize: '16px',
                            textTransform: 'capitalize'
                          })}>Save</Button>
                      </Stack>
                    }

                  </form>
                </Grid>
              </Grid>
            </Grid>
          </Grid>


        </Box>
        :
        <Box sx={{ width: "100%" }}>
          <Skeleton />
          <Skeleton animation="wave" />
          <Skeleton animation={false} />
        </Box>

      }
    </Container >
  )
}

export default SettingsCard
